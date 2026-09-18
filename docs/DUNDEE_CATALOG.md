# Dundee-Kronenbibliothek

Der aktive ODC-Katalog enthält **32 bleibende FDI-Positionen**. Die 16 eigenständigen
linken Dundee-Modelle wurden vorbereitet; die rechten Positionen sind ausdrücklich
gekennzeichnete Spiegelableitungen. Die früheren beiden Zahnkataloge bleiben unter
`Resources/data/legacy/` erhalten.

## Verwendung

ODC verwendet weiterhin `Resources/data/odc_tooth_library.blend`; bestehende
Standardpfade funktionieren damit weiter. Der Laufzeitkatalog enthält ausschließlich
die 32 exakt benannten FDI-Meshes, keine Wurzeln, Hilfskörper oder Beschriftungen.

Für den Blender Asset Browser den Ordner `Resources/data` als Asset-Bibliothek
eintragen. Die Modelle sind nach Kiefer und Zahntyp katalogisiert, mit FDI-Nummern
versehen und haben gerenderte Vorschaubilder. Die separate Übersichtsdatei
`Dundee_Katalog_32_Zaehne.blend` zeigt sie nebeneinander; ihre Layout-Transformationen
gehören nur zur Ansicht.

Nach Auswahl eines Zahns zuerst Größe, Stellung, Nachbarkontakte und Antagonisten
am konkreten Scan festlegen. Anschließend Präparationsgrenze und Einschubrichtung
kontrollieren und die Innenfläche mit dem passenden Labor-/Materialprofil erstellen.

## Was vorbereitet wurde

- Wurzeln anhand des farblich bzw. texturiert markierten Kronen-Wurzel-Übergangs
  entfernt; genau ein offener Halsrand bleibt für die spätere Innenflächenanbindung.
- Exakte Nahtduplikate verschweißt; lose Fragmente und bei 26 zusätzliche innere
  Hilfskörper entfernt.
- Originale Kronenpunkte erhalten: kein globales Glätten, Remeshing, Subdivision
  oder anisotropes Skalieren. Nur neue Schnittpunkte unter 8 µm Abstand zu einem
  direkt benachbarten Originalpunkt werden gegebenenfalls zusammengeführt.
- Identische lokale Achsen: **+X mesial, +Z okklusal/inzisal**. Bukkal liegt in
  Quadrant 1/3 auf +Y und in Quadrant 2/4 auf −Y. Objekttransformationen sind
  angewendet; der Ursprung liegt im Mittel des Halsrandes.
- Spiegelung erfolgt in lokal Y mit korrigierter Flächenreihenfolge und positiver
  Objektskalierung.
- Neutrales Material; Quellfarben separat als `SourceColor` erhalten.
- Herkunft, Lizenz, Quellhash, Maßstab und Verarbeitung stehen direkt am Asset.

Der Rand wird aus der Farbgrenze interpoliert. Geglättet wird ausschließlich das
für die Schnittlage verwendete Farbskalarfeld, nicht die Zahnoberfläche. Die feine
Unregelmäßigkeit des vorhandenen Halsrandes ist keine klinisch bestätigte
Präparationsgrenze.

## Bearbeitungsgruppen

| Gruppe | Verwendung |
|---|---|
| CEJ | Exakt der einzige offene Halsrand |
| CervicalBlend | Quintisch auslaufende Gewichte im metrischen zervikalen Band |
| AnatomyProtected | Unveränderliche obere Anatomie bei der neuen Randanpassung |
| Mesial/Distal Contact | Vorschläge für proximale Kontaktbereiche |
| Mesial/Distal Connector | Größere Bereiche für die Verbinderbearbeitung |
| Incisal Edge / Palatinal Face | Frontzahnorientierung und ODC-Okklusionshilfen |
| Buccal Cusp bzw. Mesiobuccal/Distobuccal Cusp | Höckerorientierung der Seitenzähne |
| Middle Fissure | Zentraler Fissurenbereich für ODC |
| Zusätzliche Höckergruppen | Falls am jeweiligen Quellmodell vorhanden |

Beschriftungspins der Quelle sind keine exakten CAD-Höckerspitzen. Wo erforderlich
wurden Gruppen auf kontrollierte lokale Spitzen des unveränderten Netzes gelegt.
Kontakt- und Fissurengruppen enthalten teils geometrisch abgeleitete Vorschläge.
Die Einzelherkunft jeder Gruppe steht in `Landmark evidence`.

Der neue ODC-Pfad behandelt triangulierte Kronen anhand dieser Gruppen. Er setzt
keine regelmäßigen Quad-Netzringe voraus. Ungültige Randverformungen werden vor der
Übernahme abgelehnt; dabei bleibt die vorhandene Form erhalten. Eine Ablehnung
fordert eine andere Ausgangsstellung, Randkontur oder manuelle Bearbeitung.

## Maßstab und fallbezogene Werte

Die Quellmodelle haben keinen belegten physischen Millimetermaßstab. Für gut
handhabbare Ausgangsgrößen wurden gleichmäßige Skalierungen auf folgende
**gewählte nominelle mesiodistale Breiten** verwendet:

| Linke FDI | Breite in mm | Linke FDI | Breite in mm |
|---|---:|---|---:|
| 21 | 8,5 | 31 | 5,0 |
| 22 | 6,5 | 32 | 5,5 |
| 23 | 7,5 | 33 | 7,0 |
| 24 | 7,0 | 34 | 7,0 |
| 25 | 7,0 | 35 | 7,0 |
| 26 | 10,0 | 36 | 11,0 |
| 27 | 9,0 | 37 | 10,5 |
| 28 | 8,5 | 38 | 10,0 |

Diese Werte sind Startgrößen, keine gemessenen individuellen Zahngrößen.
Spiegelpartner haben dieselbe Breite.

Zementspalt, Spacer-Beginn, Einschubachse, Unterschnittblockierung, Randstärke,
Mindestwandstärke, Fräserradius und Sinterschrumpfung sind **nicht in die
Anatomievorlagen eingebrannt**. Sie werden je Patientenfall und konkretem
KATANA-/CAM-Profil festgelegt. Eine offene Anatomievorlage ist keine fertige,
geschlossene Fertigungskrone.

## Auffällige Quellenzuordnungen

**31/32 und daraus abgeleitet 41/42 benötigen eine fachliche Identitätskontrolle.**
Die Autor-Titel nennen zentralen bzw. seitlichen unteren Schneidezahn, die
internen LL2-/LL1-Namen widersprechen ihnen. Die Inzisalasymmetrie bestätigt den
Widerspruch nicht abschließend. Der Katalog folgt nachvollziehbar den Autor-Titeln,
markiert den Hinweis aber am Asset und in der Übersicht. Die Zuordnung wird nicht
als unabhängig anatomisch verifiziert ausgegeben.

Bei 37 enthält die Quellbeschreibung einen widersprüchlichen Text; Titel, URL und
interner LL7-Name stimmen für den unteren zweiten Molaren überein. 26/16 verwenden
die anatomische Variante mit Carabelli-Höcker.

## Quellen und Lizenz

Urheber: **University of Dundee, School of Dentistry**. Alle verwendeten Modelle
stehen unter [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Die GLBs wurden über [TeethAtlas](https://www.teethatlas.com/) bezogen.
[Einzelquellen, Attribution und Hashes](../Resources/dundee/ATTRIBUTION.txt)
sowie das [strukturierte Manifest](../Resources/dundee/manifest.json) liegen bei.
Die öffentlich weiterverteilten GLBs sind mit glTF-Transform/Draco verarbeitet;
Bitidentität mit den ursprünglichen Sketchfab-Downloadarchiven wurde nicht belegt.

Änderungen: Wurzeltrimmung, Nahtbereinigung, Auswahl der äußeren Schale,
Achsenausrichtung, nominelle Skalierung, Ursprung, Spiegelableitungen,
Bearbeitungsgruppen, neutrale Darstellung und Asset-Metadaten. Die Bearbeitung
impliziert keine Unterstützung durch die ursprünglichen Autoren.

## Prüfstand vom 18.09.2026

Alle 32 Assets bestehen die Netzprüfung: je eine zusammenhängende Kronenfläche,
ein exakter CEJ-Rand, keine weiteren Öffnungen, losen Punkte, degenerierten
Dreiecke, falschen Flächenausrichtungen oder erkannten Selbstüberschneidungen.
Die 16 Originalformen wurden aus sechs Richtungen visuell geprüft, die rechten
Gegenstücke zusätzlich als exakte Spiegelungen bestätigt. 52 Höckeranker und
zwei Fossa-Anker wurden nach ihrer Anwendung geprüft. Die Gruppenkorrektur hat
keine Koordinaten, Dreiecke oder Hals-/Schutzgewichte verändert.

Import und wiederholbarer Randsitz funktionieren im CEJ-nahen synthetischen
Test für **32/32 Zähne**, mit exakt erhaltener geschützter Anatomie.
Vollbogen, Okklusionsschema und Crown-Import wurden mit der finalen Bibliothek
geprüft. Die sechs gezielten Tests des archivierten Katalogs bestehen weiterhin.

Bei einer angeforderten automatischen **6°-Konvergenz** bestehen 26 Formen die
Geometrieprüfung. Bei **12, 22, 32, 35, 42 und 45** wird die Änderung wegen
drohender scharfer Kanten oder lokaler Flächendrehung ohne Meshänderung abgelehnt.
Diese Grenze der Operation ist offen dokumentiert. Auch eine unpassende erzeugte
Innenfläche kann der Solid-Prüfer ablehnen; der vorhandene Entwurf bleibt erhalten.

[Finale unabhängige Prüfung](dundee/final_applied_audit.json),
[Prüfung der ODC-Funktionen und Grenzen](dundee/CONSUMER_VALIDATION.md),
[obere Seitenzähne rundum](dundee/upper_posterior_six_views.jpg) und
[untere Seitenzähne rundum](dundee/lower_posterior_six_views.jpg).

## Reproduzierbarer Aufbau

Blender 5.1.2 bringt die verwendeten Python-/NumPy-Funktionen und den GLB-Importer
mit. Der Aufbau benötigt weder ein Sketchfab-Konto noch einen Netzwerkzugriff:

```sh
blender -b --factory-startup --python-exit-code 1 \
  --python tools/build_dundee_catalog.py -- \
  --output /tmp/dundee.blend --work-dir /tmp/dundee-build

blender -b --factory-startup --python-exit-code 1 \
  --python tools/present_dundee_catalog.py -- \
  --library /tmp/dundee.blend --previews /tmp/dundee-previews \
  --overview /tmp/Dundee_Katalog_32_Zaehne.blend
```

Der erste Schritt prüft alle 16 Quell-SHA256-Werte, importiert und bereitet die
Netze vor, erzeugt die Spiegelpartner und schreibt Geometrie-/Gruppenprotokolle.
Der zweite ergänzt Vorschaubilder und Asset-Kategorien sowie eine separate
Übersicht. Er verändert keine Geometrie der Laufzeitbibliothek.

Installation, Neustart und Entfernen des fertigen ZIP-Pakets wurden in einem
isolierten Blender-Profil geprüft; alle drei Schritte bestanden. Das installierte
Paket lädt die32 Dundee-Assets samt Lizenz und Bearbeitungsgruppen aus dem
eigenen Standardpfad. [Paketprüfung](dundee/installation_results.json).
