"""Anatomy-preserving root trim, axes, semantic groups and mirrored assets.
Executed by build_dundee_catalog.py; no network or patient inputs.
"""
import bpy,bmesh,numpy as np,json,heapq,math,hashlib,uuid
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
(W/'prepared').mkdir(exist_ok=True)
manifest=MANIFEST;assets={a['source_left_fdi']:a for a in manifest['assets']}
# Artist-selected startup widths, not calibrated source measurements or clinical prescriptions.
NOMINAL_MD={21:8.5,22:6.5,23:7.5,24:7.0,25:7.0,26:10.0,27:9.0,28:8.5,31:5.0,32:5.5,33:7.0,34:7.0,35:7.0,36:11.0,37:10.5,38:10.0}
def adjacency(v,f):
 a=[set() for _ in v]
 for x,y,z in f:
  a[x].update((int(y),int(z)));a[y].update((int(x),int(z)));a[z].update((int(x),int(y)))
 return a
def largest(v,f,c,ids):
 adj=adjacency(v,f);unseen=set(range(len(v)));components=[]
 while unseen:
  seed=next(iter(unseen));stack=[seed];unseen.remove(seed);found=[]
  while stack:
   i=stack.pop();found.append(i)
   for j in adj[i]:
    if j in unseen:unseen.remove(j);stack.append(j)
  components.append(found)
 used=np.array(sorted(max(components,key=len)));remap=np.full(len(v),-1);remap[used]=np.arange(len(used));keep=(remap[f]>=0).all(1)
 return v[used],remap[f[keep]],c[used],ids[used],sorted([len(q) for q in components],reverse=True)
def clip(v,f,c,scalar,threshold):
 points=list(v);colors=list(c);ids=list(range(len(v)));cuts={};faces=[]
 def cross(a,b):
  key=tuple(sorted((a,b)))
  if key not in cuts:
   t=(threshold-scalar[a])/(scalar[b]-scalar[a]);cuts[key]=len(points);points.append(v[a]+t*(v[b]-v[a]));colors.append(c[a]+t*(c[b]-c[a]));ids.append(-1)
  return cuts[key]
 for tri in f:
  out=[]
  for j in range(3):
   a,b=map(int,(tri[j],tri[(j+1)%3]));ia=scalar[a]<=threshold;ib=scalar[b]<=threshold
   if ia:out.append(a)
   if ia!=ib:out.append(cross(a,b))
  for j in range(1,len(out)-1):faces.append((out[0],out[j],out[j+1]))
 used=np.unique(faces);remap=np.full(len(points),-1);remap[used]=np.arange(len(used))
 return largest(np.array(points)[used],remap[faces],np.array(colors)[used],np.array(ids)[used])
def geometry(v,f,self_check=True):
 me=bpy.data.meshes.new('validation');me.from_pydata(v.tolist(),[],f.tolist());me.update();bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
 bd=[e for e in bm.edges if e.is_boundary];ba={}
 for e in bd:
  a,b=[x.index for x in e.verts];ba.setdefault(a,[]).append(b);ba.setdefault(b,[]).append(a)
 loops=[];remaining=set(ba)
 if all(len(x)==2 for x in ba.values()):
  while remaining:
   start=min(remaining);seq=[start];prev=-1;cur=start
   while True:
    nxt=next(q for q in ba[cur] if q!=prev)
    if nxt==start:break
    seq.append(nxt);prev,cur=cur,nxt
    if len(seq)>len(ba):raise ValueError('boundary')
   remaining.difference_update(seq);loops.append(seq)
 r={'vertices':len(v),'triangles':len(f),'boundary_edges':len(bd),'boundary_loops':len(loops),'boundary_bad_degree':sum(len(x)!=2 for x in ba.values()),'nonmanifold_edges_excluding_boundary':sum(not e.is_manifold and not e.is_boundary for e in bm.edges),'degenerate_faces':sum(x.calc_area()<1e-12 for x in bm.faces),'euler':len(bm.verts)-len(bm.edges)+len(bm.faces),'inconsistent_winding_edges':sum(e.is_manifold and e.link_loops[0].vert==e.link_loops[1].vert for e in bm.edges)}
 if self_check:
  sets=[set(t) for t in f];bt=BVHTree.FromPolygons(v.tolist(),f.tolist(),all_triangles=True);r['nonadjacent_self_intersections']=sum(a<b and not sets[a]&sets[b] for a,b in bt.overlap(bt))
 bm.free();bpy.data.meshes.remove(me);return r,loops
def valid(r):return r['boundary_loops']==1 and not r['boundary_bad_degree'] and not r['nonmanifold_edges_excluding_boundary'] and not r['degenerate_faces'] and not r['inconsistent_winding_edges'] and r['euler']==1 and not r.get('nonadjacent_self_intersections',0)
def metric(v,adj,seeds,limit=float('inf')):
 dist=np.full(len(v),np.inf);heap=[]
 for i in seeds:dist[i]=0;heapq.heappush(heap,(0,int(i)))
 while heap:
  d,i=heapq.heappop(heap)
  if d>dist[i] or d>limit:continue
  for j in adj[i]:
   q=d+float(np.linalg.norm(v[i]-v[j]))
   if q<dist[j] and q<=limit:dist[j]=q;heapq.heappush(heap,(q,j))
 return dist
def canonical(fdi):
 if fdi<=23:return np.diag([-1,1,-1])
 if fdi==26:return np.diag([1,-1,-1])
 if fdi<=28:return np.array([[0,-1,0],[-1,0,0],[0,0,-1]])
 if fdi<=33:return np.diag([-1,-1,1])
 return np.array([[0,-1,0],[1,0,0],[0,0,1]])
def smoothstep(x):x=np.clip(x,0,1);return x*x*x*(x*(x*6-15)+10)
bpy.ops.wm.read_factory_settings(use_empty=True);prepared=[];reports=[]
for fdi in sorted(assets):
 if fdi==26:
  external=W/'tooth26/crown_no_root.npz'
  if not external.exists():raise FileNotFoundError(external)
  d=np.load(external);cv=d['world_vertices'];cf=d['faces'];cc=d['colors'];ci=d['source_vertex_indices'];threshold=float(d['threshold']) if 'threshold'in d else .20;source=json.loads((W/'import_report.json').read_text());bounds=np.array(next(x for x in source if x['fdi']==26)['full_bounds']);source_center=bounds.mean(0);clean_info={'external_texture_preparation':True}
 else:
  d=np.load(W/'imported'/f'{fdi}_source.npz');sv=d['world_vertices'];sf=d['faces'];sc=d['colors'];source_center=(sv.min(0)+sv.max(0))/2;sv,sf,sc,ids,srccomps=largest(sv,sf,sc,np.arange(len(sv)));adj=adjacency(sv,sf)
  scalar=sc[:,0]-sc[:,2];original_scalar=scalar.copy()
  for step in range(4):scalar=.4*scalar+.6*np.array([scalar[list(n)].mean() for n in adj])
  selected=None;attempts=[]
  for threshold in [.12,.14,.16,.18,.10]:
   cv,cf,cc,ci,comps=clip(sv,sf,sc,scalar,threshold);tr,loops=geometry(cv,cf);attempts.append({'threshold':threshold,**tr})
   if valid(tr):selected=True;break
  assert selected,(fdi,attempts)
  ci[ci>=0]=ids[ci[ci>=0]]
  clean_info={'source_component_vertex_counts':srccomps,'clipped_component_vertex_counts':comps,'color_scalar_smoothing_steps':4,'geometry_smoothing':False,'threshold_attempts':attempts}
 C=canonical(fdi);v=cv@C.T;scale=NOMINAL_MD[fdi]/np.ptp(v[:,0]);v*=scale
 r,loops=geometry(v,cf);assert valid(r),(fdi,r);bd=np.array(loops[0]);origin=v[bd].mean(0);v-=origin
 # Collapse only newly interpolated cut vertices that almost coincide with an existing source vertex.
 # Existing enamel vertices are never moved.
 adj=adjacency(v,cf);remap=np.arange(len(v));snapped=[]
 for i in np.flatnonzero(ci<0):
  candidates=[j for j in adj[i] if ci[j]>=0]
  if not candidates:continue
  j=min(candidates,key=lambda j:np.linalg.norm(v[i]-v[j]));distance=float(np.linalg.norm(v[i]-v[j]))
  if distance<.008:remap[i]=j;snapped.append((int(i),int(j),distance))
 trial=remap[cf];keep=np.array([len(set(q))==3 for q in trial]);trial=trial[keep];used=np.unique(trial);ix=np.full(len(v),-1);ix[used]=np.arange(len(used));trial=ix[trial];tr,tl=geometry(v[used],trial)
 if valid(tr):
  v=v[used];cf=trial;cc=cc[used];ci=ci[used];r=tr;bd=np.array(tl[0])
 else:snapped=[]
 # Origin stays tied to actual final CEJ centroid, with no vertex shape deformation.
 recenter=v[bd].mean(0);v-=recenter;origin+=recenter
 me=bpy.data.meshes.new(f'Dundee_{fdi}_Crown');me.from_pydata(v.tolist(),[],cf.tolist());me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
 bm.to_mesh(me);bm.free();cf=np.array([tuple(f.vertices) for f in me.polygons]);r,loops=geometry(v,cf);assert valid(r),(fdi,r);bd=np.array(loops[0])
 ob=bpy.data.objects.new(str(fdi),me);bpy.context.scene.collection.objects.link(ob)
 for f in me.polygons:f.use_smooth=True
 ca=me.color_attributes.new(name='SourceColor',type='FLOAT_COLOR',domain='POINT')
 for cl,color in zip(ca.data,cc):cl.color=color
 adj=adjacency(v,cf);height=float(v[:,2].max());band=min(3.,max(1.5,.4*height));distance=metric(v,adj,bd);weights=smoothstep(1-distance/band);weights[bd]=1.
 kd=KDTree(len(v))
 for i,q in enumerate(v):kd.insert(Vector(q),i)
 kd.balance()
 groups={};evidence={}
 def addgroup(name,indices,values=None,why='geometry-derived proposal'):
  override=assets[fdi].get('cad_landmark_overrides',{}).get(name)
  if override and name!='Middle Fissure':
   anchor=int(override['prepared_vertex_index'])
   assert np.linalg.norm(v[anchor]-override['prepared_coordinate_mm'])<1.e-5,(fdi,name,'reviewed landmark geometry changed')
   indices=patch(v[anchor],float(override['suggested_patch_radius_mm']))
   why='Reviewed local cusp maximum on unchanged source mesh; vertex '+str(anchor)
  indices=sorted(set(map(int,indices)));assert indices,(fdi,name);g=ob.vertex_groups.new(name=name)
  if values is None:g.add(indices,1.,'REPLACE')
  else:
   for i in indices:g.add([i],float(values[i]),'REPLACE')
  groups[name]=indices;evidence[name]=why
 def patch(point,radius):
  seed=kd.find(Vector(point))[1];return np.flatnonzero(metric(v,adj,[seed],radius)<=radius)
 addgroup('CEJ',bd,why='ordered boundary at source crown/root transition')
 addgroup('CervicalBlend',np.flatnonzero(weights>0),weights,'quintic taper of metric surface distance from CEJ')
 addgroup('AnatomyProtected',np.flatnonzero(weights==0),why='outside prepared cervical deformation band')
 addgroup('Cervical Band',np.flatnonzero(weights>0),why='editable cervical band')
 pins={}
 for pin in assets[fdi]['annotation_pins']:
  x,y,z=pin['position_gltf_centered'];world=source_center+np.array([x,-z,y]);pins[pin['label']]=world@C.T*scale-origin
 def sourcepoint(labels):
  for label in labels:
   if label in pins:return pins[label],label
  return None,None
 family='incisor' if fdi%10<3 else 'canine' if fdi%10==3 else 'premolar' if fdi%10<6 else 'molar'
 buccal_sign=-1 if fdi//10==2 else 1
 for side,sgn in [('Mesial',1),('Distal',-1)]:
  point,label=sourcepoint([side+' Contact Point'])
  if point is None:
   candidates=np.flatnonzero((v[:,2]>height*.45)&(v[:,2]<height*.86));seed=candidates[np.argmax(v[candidates,0]*sgn)];point=v[seed];label='geometric proximal extremum in coronal height range'
  addgroup(side+' Contact',patch(point,.4),why=label)
  addgroup(side+' Connector',patch(point,.9),why=label+'; broader editable patch')
 if family in ['incisor','canine']:
  addgroup('Incisal Edge',np.flatnonzero(v[:,2]>=height-(.32 if family=='incisor' else .28)),why='coronal ridge/extreme region; canine compatibility alias')
  if family=='canine':addgroup('Cusp Tip',groups['Incisal Edge'],why='canine cusp region')
  point,label=sourcepoint(['Palatal Surface','Lingual Surface','Longitudinal Ridge','Cingulum'])
  if point is None:
   candidates=np.flatnonzero((v[:,2]>height*.35)&(v[:,2]<height*.8));point=v[candidates[np.argmin(v[candidates,1]*buccal_sign)]];label='geometry-derived lingual surface proposal'
  addgroup('Palatinal Face',patch(point,.7),why=label)
 else:
  if family=='premolar':
   point,label=sourcepoint(['Buccal Cusp Tip','Buccal Cusp'])
   assert point is not None,fdi
   addgroup('Buccal Cusp',patch(point,.38),why=label)
  else:
   for name,label in [('Mesiobuccal Cusp','Mesio-Buccal Cusp'),('Distobuccal Cusp','Disto-Buccal Cusp')]:
    assert label in pins,(fdi,label);addgroup(name,patch(pins[label],.4),why=label)
  point,label=sourcepoint(['Mesio-Distal Fissure','Central Fossa','Central Pit'])
  if point is None:
   # Central coronal surface valley; label as a proposal, not an authored annotation.
   norm=np.array([tuple(q.normal) for q in me.vertices]);extent=np.ptp(v,axis=0)
   candidates=np.flatnonzero((np.abs(v[:,0])<extent[0]*.24)&(np.abs(v[:,1])<extent[1]*.24)&(v[:,2]>height*.5)&(norm[:,2]>.15))
   assert len(candidates),(fdi,'fossa candidate');point=v[candidates[np.argmin(v[candidates,2])]];label='geometry-derived central occlusal valley proposal'
  addgroup('Middle Fissure',patch(point,.45),why=label)
  point,label=sourcepoint(['Palatal Cusp','Mesio-Palatal Cusp','Lingual Cusp','Mesio-Lingual Cusp'])
  if point is not None:addgroup('Palatinal Cusp',patch(point,.38),why=label)
  if 'Cusp of Carabelli'in pins:addgroup('Cusp of Carabelli',patch(pins['Cusp of Carabelli'],.35),why='Cusp of Carabelli source annotation')
 ma=bpy.data.materials.get('Dundee | Neutral enamel') or bpy.data.materials.new('Dundee | Neutral enamel');ma.diffuse_color=(.79,.76,.68,1);me.materials.append(ma)
 a=assets[fdi];meta={'odc_library':'dundee','odc_topology':'triangulated_crown','FDI':str(fdi),'Tooth family':family,'Jaw':'maxillary' if fdi<30 else 'mandibular','Side':'left','Author':a['author'],'License':'CC BY 4.0','License URL':a['license_url'],'Source URL':a['source_url'],'Source SHA256':a['sha256'],'Source filename':a['file'],'Nominal MD mm':NOMINAL_MD[fdi],'Uniform source scale':scale,'Scale status':'Artist-selected nominal startup size; physical source scale uncalibrated','Preparation':'Dundee catalog v1: exact seam weld, source-component cleanup, color/texture root trim, sub-8um cut-vertex conditioning; no enamel smoothing','Root threshold':threshold,'Cervical band mm':band,'Landmarks':'Source annotation patches or explicit geometric proposals; verify for each case','Clinical profile':'Outer anatomy only; no spacer, intaglio, material or CAM allowance baked in'}
 if fdi in (31,32):meta['Source identification review']='Author title and internal LL1/LL2 node labels conflict; catalogue follows author title. Anatomical identity requires review.'
 for k,value in meta.items():ob[k]=value
 ob['Landmark evidence']=json.dumps(evidence,ensure_ascii=False)
 ob.asset_mark();ob.asset_data.catalog_id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/ZAP-Wunschlachen/odc_public/dundee/'+meta['Jaw']+'/'+family));ob.asset_data.author='University of Dundee, School of Dentistry';ob.asset_data.description=f'FDI {fdi}, Dundee {family}. Root removed; prepared CEJ and protected anatomy. CC BY4.0. Nominal mm size, case-specific fitting required.'
 for tag in [str(fdi),'Dundee',family,'left',meta['Jaw'],'CC BY4.0']:ob.asset_data.tags.new(tag)
 np.savez(W/'prepared'/f'{fdi}.npz',vertices=v,faces=cf,colors=cc,boundary=bd,cervical_weights=weights,source_vertex_indices=ci,source_to_canonical=C,uniform_scale=scale,canonical_origin=origin)
 details={'fdi':fdi,**r,'threshold':threshold,'nominal_md_mm':NOMINAL_MD[fdi],'uniform_scale':scale,'bounds':[v.min(0).tolist(),v.max(0).tolist()],'origin_mean_cej_error_mm':float(np.linalg.norm(v[bd].mean(0))),'protected_vertices':int((weights==0).sum()),'cervical_band_mm':band,'snapped_new_cut_vertices':len(snapped),'maximum_cut_snap_mm':max([x[2] for x in snapped],default=0),'source_enamel_vertices_moved':0,'groups':{name:{'count':len(ids),'centroid':v[ids].mean(0).tolist(),'evidence':evidence[name]} for name,ids in groups.items()},'cleanup':clean_info}
 (W/'prepared'/f'{fdi}.json').write_text(json.dumps(details,indent=2));reports.append(details);prepared.append(ob);print('PREPARED',fdi,len(v),len(cf),len(bd),flush=True)
 # True counterpart reflection across local Y; no negative object scale.
 right=fdi-10 if fdi<30 else fdi+10;mirror=ob.copy();mirror.data=me.copy();mirror.name=str(right);bpy.context.scene.collection.objects.link(mirror)
 for vert in mirror.data.vertices:vert.co.y*=-1
 bm=bmesh.new();bm.from_mesh(mirror.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(mirror.data);bm.free()
 mirror['FDI']=str(right);mirror['Side']='right';mirror['Mirrored from FDI']=str(fdi);mirror.asset_mark();mirror.asset_data.catalog_id=ob.asset_data.catalog_id;mirror.asset_data.author='University of Dundee, School of Dentistry';mirror.asset_data.description=f'FDI {right}, mirrored from Dundee FDI{fdi}. Prepared crown surface; CC BY4.0. Nominal mm size.'
 for tag in [str(right),'Dundee',family,'right',meta['Jaw'],'mirrored','CC BY4.0']:mirror.asset_data.tags.new(tag)
 prepared.append(mirror)
s=bpy.context.scene;s.name='Dundee | Runtime assets';s.unit_settings.system='METRIC';s.unit_settings.scale_length=.001;s.unit_settings.length_unit='MILLIMETERS'
(W/'prepared_report.json').write_text(json.dumps(reports,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT));print('CATALOG_PREPARED',len(prepared),flush=True)
