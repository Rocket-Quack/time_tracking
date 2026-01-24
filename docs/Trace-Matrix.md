# Trace Matrix - Time Tracking App vs Anforderungen

Datum: 2026-01-24
Quelle: Statische Code- und Artefaktpruefung (kein laufendes System)
Scope: Abgleich der App gegen Anforderungen in:
- docs/Anforderungen-Stichpunkte.md
- docs/MVP-Anforderungen.md
- docs/Fachliche-Anforderungen.md

Legende Status:
- Erfuellt: Funktion im Code/Artefakt vorhanden
- Teilweise: Grundfunktion vorhanden, aber Luecken/Abweichungen
- Offen: Nicht gefunden
- Unklar: Nur ueber Frappe-Standard moeglich, keine App-spezifische Umsetzung

---

## 1) Anforderungen-Stichpunkte (Anforderungen-Stichpunkte.md)

| ID | Anforderung (Kurz) | Status | Evidenz / Fundstelle | Hinweise / Gap |
|---|---|---|---|---|
| AS-1 | Online-Zeiterfassung fuer interne/externe Mitarbeiter | Teilweise | Rollen/Profiles: time_tracking/fixtures/role.json; time_tracking/time_tracking/doctype/time_tracking_profile/time_tracking_profile.json | Kein explizites Konzept fuer externe Mitarbeiter, nur Rollen/Profiles. |
| AS-2 | Mitarbeiter waehlen Projekte fuer schnelle Buchung | Erfuellt | Project Assignments + Duplikat-Validierung: time_tracking/time_tracking/doctype/time_tracking_profile/time_tracking_profile.json; UI in weekly_booking mit Dropdown: time_tracking/time_tracking/page/weekly_booking/weekly_booking.js | Projektauswahl basiert auf Profil-Zuweisung; Mehrfachzuordnung wird validiert. |
| AS-3 | Projektadministration: Root-Element SSS | Offen | time_tracking/time_tracking/doctype/time_tracking_project/time_tracking_project.json | Kein erzwungenes Root-Projekt oder Auto-Seed. |
| AS-4 | Projekte als Baumstruktur mit Parent | Erfuellt | is_tree + parent_time_tracking_project: time_tracking/time_tracking/doctype/time_tracking_project/time_tracking_project.json; Tree UI: time_tracking/time_tracking/doctype/time_tracking_project/time_tracking_project_tree.js |  |
| AS-5 | Wochenansicht: aktuelle Buchungen + Vorwoche als Vorlage + neue Eintraege | Erfuellt | weekly booking UI + previous week suggestions: time_tracking/time_tracking/page/weekly_booking/weekly_booking.js, weekly_booking.py | Vorschlaege werden geladen und angezeigt. |
| AS-6 | Berichtswesen: Berichte individuell erstellen und spaeter aufrufen | Offen | Reports vorhanden, aber kein Report-Builder / Saved Reports: time_tracking/time_tracking/report/ | Frappe Standard kann speichern, aber nicht App-spezifisch umgesetzt. |
| AS-7 | Export Excel aus Bericht | Teilweise | Frappe Standard-Export moeglich; keine eigene Excel-Formatierung | Kein explizites .xlsx Layout wie gefordert. |
| AS-8 | Druckbare Stundenabrechnung aus Bericht | Teilweise | Print Format fuer Single Booking Service Report: time_tracking/fixtures/print_format.json | Nur ein spezifischer Report, Layout nicht identisch mit Anforderung. |

---

## 2) MVP-Anforderungen (MVP-Anforderungen.md)

### 2.1 Benutzerverwaltung (vereinfacht)
| ID | Anforderung (Kurz) | Status | Evidenz / Fundstelle | Hinweise / Gap |
|---|---|---|---|---|
| MVP-U-1 | Rollen: Administrator + Mitarbeiter | Teilweise | Rollen vorhanden: time_tracking/fixtures/role.json | Rollen heissen Time Tracking Admin/Employee/Manager, aber kein separater Admin/Mitarbeiter-Flow im App-UI. |
| MVP-U-2 | Profilfelder: Username/Name/Email/Passwort/Status | Unklar | Frappe User DocType (Standard) | App definiert Profile, nicht Benutzerverwaltung. |
| MVP-U-3 | Login/Logout, Passwort aendern | Unklar | Frappe Standard | Keine App-spezifischen Screens. |
| MVP-U-4 | Admin kann Benutzer anlegen/deaktivieren | Unklar | Frappe Standard | Keine App-spezifische UI. |

### 2.2 Projektverwaltung (vereinfacht)
| ID | Anforderung (Kurz) | Status | Evidenz / Fundstelle | Hinweise / Gap |
|---|---|---|---|---|
| MVP-P-1 | Root-Element SSS | Offen | time_tracking/time_tracking/doctype/time_tracking_project/time_tracking_project.json | Kein Root erzwungen. |
| MVP-P-2 | Parent-Child Baumstruktur | Erfuellt | is_tree + parent_time_tracking_project: time_tracking/time_tracking/doctype/time_tracking_project/time_tracking_project.json |  |
| MVP-P-3 | Pflichtfelder: Name, optional Description, Parent | Erfuellt | Felder project_name, project_description, parent_time_tracking_project |  |
| MVP-P-4 | Status Aktiv/Inaktiv | Erfuellt | project_status Select: time_tracking/time_tracking/doctype/time_tracking_project/time_tracking_project.json; List View Indicator: time_tracking/time_tracking/doctype/time_tracking_project/time_tracking_project_list.js | Status steuerbar; Buchbarkeit separat ueber not_bookable. |
| MVP-P-5 | Projektsuche (Text, Status, Baum) | Teilweise | Tree-View + Suchfelder: time_tracking/time_tracking/doctype/time_tracking_project/time_tracking_project_tree.js; search_fields: time_tracking_project.json | Kein expliziter Status-Filter. |

### 2.3 Zeitbuchung (Kern)
| ID | Anforderung (Kurz) | Status | Evidenz / Fundstelle | Hinweise / Gap |
|---|---|---|---|---|
| MVP-T-1 | Wochenansicht UI mit Woche vor/zurueck/Heute | Erfuellt | weekly_booking UI: time_tracking/time_tracking/page/weekly_booking/weekly_booking.js |  |
| MVP-T-2 | Projekt- und Kommentarspalte, 7 Tage, Summen | Erfuellt | weekly_booking.js + weekly_booking.html |  |
| MVP-T-3 | Stundenformat H:MM oder Dezimal | Teilweise | UI akzeptiert H:MM oder Dezimal, speichert Stunden als Float; Validierung auf Inkrement in Minuten | Speichert intern Minuten, Anzeige H:MM. |
| MVP-T-4 | Validierung: positiv, Projekt aktiv, Pflichtfelder | Teilweise | time_booking.py validiert positiv, not_bookable, Project required, Note required | Aktiv/Inaktiv vorhanden, Buchbarkeit separat; keine explizite Status-Filter in Suche. |
| MVP-T-5 | Zeilen loeschen | Erfuellt | weekly_booking.js (Row delete) |  |
| MVP-T-6 | Speichern/Abbrechen | Teilweise | Save vorhanden; kein Abbrechen-Button |  |
| MVP-T-7 | Navigation zwischen Wochen | Erfuellt | weekly_booking.js |  |
| MVP-T-8 | Projektauswahl hierarchisch | Teilweise | Projects im Dropdown, aber ohne visuelle Einrueckung | Kein hierarchisches Rendering im Dropdown. |

### 2.4 Berichtswesen (vereinfacht)
| ID | Anforderung (Kurz) | Status | Evidenz / Fundstelle | Hinweise / Gap |
|---|---|---|---|---|
| MVP-R-1 | Standard-Zeitbericht mit Zeitraum/Projekt/User-Filter | Teilweise | Service Report/Single Booking Report: time_tracking/time_tracking/report/service_report/service_report.js/.py | Filter vorhanden, Summenbildung fehlt. |
| MVP-R-2 | Ausgabe Datum, Mitarbeiter, Projekt, Kommentar, Stunden | Erfuellt | service_report.py, single_booking_service_report.py |  |
| MVP-R-3 | Admin sieht alle, Mitarbeiter nur eigene | Teilweise | single_booking_service_report.json Rollen nur Admin/System; service_report hat keine Rollenlogik im SQL | Zugriff haengt von Frappe Rollen/Perms ab. |
| MVP-R-4 | Summen (Tag/Mitarbeiter/Projekt/Gesamt) | Offen | Reports liefern rohe Zeilen | Keine Aggregations-Summen im Report. |

### 2.5 Export (Kern)
| ID | Anforderung (Kurz) | Status | Evidenz / Fundstelle | Hinweise / Gap |
|---|---|---|---|---|
| MVP-E-1 | Excel Export (xlsx) mit festem Layout | Teilweise | Frappe Standard Export moeglich | Kein spezielles Excel-Layout implementiert. |
| MVP-E-2 | PDF Export mit Layout | Teilweise | Print Format fuer Single Booking Service Report: time_tracking/fixtures/print_format.json | Layout ok fuer einen Report, kein generischer PDF-Export. |

### 2.6 Technische/UX (MVP)
| ID | Anforderung (Kurz) | Status | Evidenz / Fundstelle | Hinweise / Gap |
|---|---|---|---|---|
| MVP-TN-1 | Auth/Autorisierung Admin vs Mitarbeiter | Teilweise | Rollen in fixtures, Profile permissions | Keine App-spezifische Policy ausser Profile-Checks. |
| MVP-TN-2 | Responsive Grundfunktion | Teilweise | weekly_booking hat horizontales Scrolling | Keine expliziten mobile Layouts. |

---

## 3) Fachliche Anforderungen (Fachliche-Anforderungen.md)

### 3.1 Benutzerverwaltung
| ID | Anforderung (Kurz) | Status | Evidenz / Fundstelle | Hinweise / Gap |
|---|---|---|---|---|
| FA-U-1 | Rollen: User, Time User, Reporter, Punch User, Project Manager, Memorized Sheet User | Offen | fixtures nur 3 Rollen | Nur Time Tracking Employee/Admin/Manager vorhanden. |
| FA-U-2 | Gruppen fuer Projektzugriff | Offen | Keine Gruppen-DocType/Logik | Zugriff ueber Profilzuweisung, nicht Gruppen. |
| FA-U-3 | Entry Screens konfigurierbar | Offen | time_tracking_settings.json hat nur booking increment/format | Kein UI fuer Entry Screens. |
| FA-U-4 | Approval Plans / Period Assignments | Offen | Keine DocTypes/Logik |  |
| FA-U-5 | User Bill/Pay Rate + weitere Felder | Teilweise | Felder in Time Tracking Profile vorhanden | Viele Felder vorhanden, aber keine UI/Prozesse wie im Dokument. |
| FA-U-6 | Einstellungen kopieren | Offen | Keine Funktion |  |

### 3.2 Projektverwaltung
| ID | Anforderung (Kurz) | Status | Evidenz / Fundstelle | Hinweise / Gap |
|---|---|---|---|---|
| FA-P-1 | Root-Element SSS / hierarchisch beliebig tief | Teilweise | Tree ist vorhanden | Root nicht erzwungen. |
| FA-P-2 | Status Loggable/Reportable/Hidden | Teilweise | project_status Active/Inactive + not_bookable: time_tracking/time_tracking/doctype/time_tracking_project/time_tracking_project.json | Loggable/Reportable/Hidden fehlen; Aktiv/Inaktiv und Buchbarkeit getrennt. |
| FA-P-3 | Gruppen-Zuordnung fuer Projekte | Offen | Keine Gruppen |  |
| FA-P-4 | Custom Fields (Priority, Budget, Start/End, etc.) | Teilweise | Budget, Start/End fehlen; Budgetfelder vorhanden | Einige Felder vorhanden, aber nicht alle geforderten. |
| FA-P-5 | Projektsuche mit Filter, Tree in Ergebnissen | Teilweise | Tree View vorhanden | Filter (Status/Groups) fehlen. |
| FA-P-6 | Batch Modification, Copy Settings | Offen | Keine Funktion |  |

### 3.3 Zeitbuchung
| ID | Anforderung (Kurz) | Status | Evidenz / Fundstelle | Hinweise / Gap |
|---|---|---|---|---|
| FA-T-1 | Wochenansicht mit Toolbar/Navigation | Teilweise | weekly_booking page vorhanden | Kein kompletter Toolbar wie im Dokument (Time/Expense/Reports/Approvals). |
| FA-T-2 | Current/Memorized/New Bereiche | Teilweise | Vorschlaege aus Vorwoche vorhanden | Kein separater Bereich/Status, aber Vorschlag-Farbmarkierung. |
| FA-T-3 | Bill Type / Pay Type / Task | Offen | Keine Felder in Weekly Booking |  |
| FA-T-4 | Sheet Status + Submit for Approval | Offen | Kein Workflow |  |
| FA-T-5 | Leave Requests/Approvals/History Sidebars | Offen | Keine Sidebar-Funktionen |  |
| FA-T-6 | Validierungen (Format, negativ, loggable, Zeitraum, hohe Stunden) | Teilweise | Negativ/Increment/Project validiert | Keine Validierung auf unuebliche Stunden, Zeitraum nur Week. |

### 3.4 Berichte
| ID | Anforderung (Kurz) | Status | Evidenz / Fundstelle | Hinweise / Gap |
|---|---|---|---|---|
| FA-R-1 | Report Builder mit umfangreichen Filtern | Offen | Keine Report-Builder UI |  |
| FA-R-2 | Berichtsausgabe inkl. Spalten/Grouping | Teilweise | Service Report liefert Daten | Kein komplexes Grouping / Subtotals. |
| FA-R-3 | HTML/PDF Export Optionen | Teilweise | Print Format Single Booking | Keine generischen Optionen. |
| FA-R-4 | Gespeicherte/Scheduled/System Reports | Offen | Nicht vorhanden |  |

### 3.5 Export
| ID | Anforderung (Kurz) | Status | Evidenz / Fundstelle | Hinweise / Gap |
|---|---|---|---|---|
| FA-E-1 | Excel Export mit Layout/Formatierung | Offen | Keine Implementierung |  |
| FA-E-2 | PDF Export mit Firmenkopf, Gruppierung | Teilweise | Single Booking Print Format | Kein Firmenkopf/Logo, keine Arbeitspaket-Gruppierung wie gefordert. |
| FA-E-3 | CSV/JSON/HTML optional | Offen | Nicht implementiert |  |

### 3.6 Approvals / Integrationen / Security
| ID | Anforderung (Kurz) | Status | Evidenz / Fundstelle | Hinweise / Gap |
|---|---|---|---|---|
| FA-A-1 | Approval Workflow | Offen | Keine DocTypes/Logik |  |
| FA-I-1 | MS Project/QuickBooks Integration | Offen | Keine Integrationen |  |
| FA-I-2 | REST API / Webhook | Offen | Keine Endpoints |  |
| FA-S-1 | Audit-Log spezifisch | Offen | Kein App-spezifischer Audit | Frappe hat System-Logs, aber nicht hier verankert. |

---

## 4) Zusammenfassung (Kurz)
- Erfuellt: Wochenbuchung (Basis), Projekthierarchie, Projektstatus Aktiv/Inaktiv, Projektzuweisung ueber Profile, einfache Reports, PDF-Printformat fuer einen Report.
- Teilweise: Rollen/Benutzerverwaltung (haengt an Frappe), Report-Summen, Exporte (Excel/PDF), detaillierte Zeitbuchungs-UX.
- Offen: Approvals, Gruppenrechte, Report Builder, Integrationen, Audit/Compliance, viele fachliche Detailfelder.

Wenn gewuenscht: Ich kann als naechsten Schritt eine priorisierte Gap-Liste oder eine Umsetzungs-Roadmap aus der Matrix ableiten.
