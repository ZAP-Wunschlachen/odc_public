"""Every exposed operator poll must tolerate normal empty/partial scene states."""
import sys,json
from pathlib import Path
import bpy,addon_utils
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
module=addon_utils.enable(ROOT.name,default_set=True,persistent=False)
assert module
# Inspect the enabled package, not a potentially stale development inventory.
operators={}
for owner_name, owner in list(sys.modules.items()):
    if owner_name != ROOT.name and not owner_name.startswith(ROOT.name+'.'):
        continue
    for klass in vars(owner).values():
        if (not isinstance(klass,type) or not issubclass(klass,bpy.types.Operator)
                or not klass.__module__.startswith(ROOT.name) or not klass.is_registered):
            continue
        name=klass.bl_idname
        category,identifier=name.split('.',1)
        op=getattr(getattr(bpy.ops,category),identifier)
        assert op.get_rna_type().identifier == klass.bl_rna.identifier
        operators[name]=(op,klass)
assert len(operators)>=118, len(operators)
for obj in list(bpy.data.objects):bpy.data.objects.remove(obj,do_unlink=True)
results=[]
for context in ['empty','mesh_selected','restoration_planned']:
    if context=='mesh_selected':bpy.ops.mesh.primitive_cube_add()
    if context=='restoration_planned':bpy.ops.opendental.add_tooth_restoration(name='25')
    failures=[]
    for name,(op,klass) in operators.items():
        try:
            # Blender's operator proxy logs Python poll errors but returns False.
            # Calling the class hook first makes these failures observable.
            if 'poll' in klass.__dict__:klass.poll(bpy.context)
            op.poll()
        except Exception as error:failures.append({'operator':name,'error':str(error)})
    results.append({'context':context,'checked':len(operators),'failures':failures})
addon_utils.disable(ROOT.name,default_set=True)
p=ROOT/'tests/artifacts/poll_contexts.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(results,indent=2))
print('ODC_POLL_RESULTS',json.dumps(results),flush=True)
if any(r['failures'] for r in results):raise SystemExit(1)
