<?php
// Veröffentlichen aus der Prüfseite (intern/pruefen.html): nimmt nur die Veröffentlichungsdatei an (wiz-veroeffentlichung-1,
// zusammengefasste Zahlen ohne Einzelangaben) und legt sie als ../veroeffentlicht/aktuell.json ab; die vorige Fassung
// bleibt als vorher.json und lässt sich zurückholen ({"aktion": "zurueck"}). Der Ordner /intern/ ist per Passwort
// geschützt (Plesk). Der tägliche Lauf holt aktuell.json, prüft sie mit tools/veroeffentlichen.py (volle Sperre, Umrisse
// der Gebäude) und baut damit die Seite „Wohnen und Eigentum“. Dieses Skript prüft Form und grobe Sperrregeln vorab.
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

const FORMAT = 'wiz-veroeffentlichung-1';
const DATEIEN = ['eigentum_gebaeude.geojson', 'eigentum_anteile_ortsbezirk.json', 'mieten_aggregiert.json'];
const PFLICHT = ['eigentum_gebaeude.geojson', 'eigentum_anteile_ortsbezirk.json'];
const VERBOTEN = ['name_privat_enc', 'name_privat', 'angabe_id', 'erfassung_id', 'nettokalt_eur', 'wohnflaeche_m2', 'eur_je_m2',
    'einwilligung', 'erfasser', 'vermieter_schluessel', 'bemerkung', 'lage_hinweis', 'beleg_url', 'letzte_erhoehung_jahr', 'ausstattung'];
const GROESSE_MAX = 5000000;

function antwort(int $code, array $daten): void
{
    http_response_code($code);
    echo json_encode($daten, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function schluessel(mixed $x, array &$out): void
{
    if (!is_array($x)) {
        return;
    }
    foreach ($x as $k => $v) {
        if (is_string($k)) {
            $out[$k] = true;
        }
        schluessel($v, $out);
    }
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    antwort(405, ['ok' => false, 'fehler' => 'Nur Veröffentlichen aus der Prüfseite (POST).']);
}
// Nur aus der eigenen Seite: Der Browser schickt das gespeicherte Passwort sonst auch bei Anfragen fremder Seiten mit.
$herkunft = $_SERVER['HTTP_ORIGIN'] ?? '';
$host = $_SERVER['HTTP_HOST'] ?? '';
if ($herkunft === '' || parse_url($herkunft, PHP_URL_HOST) !== preg_replace('/:\d+$/', '', $host)
    || ($_SERVER['HTTP_SEC_FETCH_SITE'] ?? 'same-origin') !== 'same-origin') {
    antwort(403, ['ok' => false, 'fehler' => 'Nur aus der Prüfseite dieser Domain.']);
}
if (stripos($_SERVER['CONTENT_TYPE'] ?? '', 'application/json') !== 0) {
    antwort(415, ['ok' => false, 'fehler' => 'Erwartet wird JSON.']);
}
$roh = file_get_contents('php://input', false, null, 0, GROESSE_MAX + 1);
if ($roh === false || strlen($roh) > GROESSE_MAX) {
    antwort(413, ['ok' => false, 'fehler' => 'Datei zu groß.']);
}
$d = json_decode($roh, true, 64);
if (!is_array($d)) {
    antwort(400, ['ok' => false, 'fehler' => 'Kein gültiges JSON.']);
}

$ordner = dirname(__DIR__) . '/veroeffentlicht';
$aktuell = $ordner . '/aktuell.json';
$vorher = $ordner . '/vorher.json';
if (!is_dir($ordner) && !mkdir($ordner, 0755, true)) {
    antwort(500, ['ok' => false, 'fehler' => 'Ordner veroeffentlicht nicht anlegbar.']);
}
$stand = static fn(string $p): ?string => is_file($p) ? (json_decode((string) file_get_contents($p), true)['stand'] ?? null) : null;

if (($d['aktion'] ?? '') === 'zurueck') {
    if (!is_file($vorher)) {
        antwort(409, ['ok' => false, 'fehler' => 'Es gibt keine vorige Fassung.']);
    }
    $tausch = $ordner . '/.tausch.json';
    if (!rename($vorher, $tausch) || (is_file($aktuell) && !rename($aktuell, $vorher)) || !rename($tausch, $aktuell)) {
        antwort(500, ['ok' => false, 'fehler' => 'Zurückholen gescheitert.']);
    }
    antwort(200, ['ok' => true, 'aktion' => 'zurueck', 'stand' => $stand($aktuell), 'vorher' => $stand($vorher)]);
}

// Form
if (($d['format'] ?? '') !== FORMAT || !is_array($d['dateien'] ?? null)) {
    antwort(422, ['ok' => false, 'fehler' => 'Keine Veröffentlichungsdatei der Prüfseite.']);
}
if (!empty($d['probe'])) {
    antwort(422, ['ok' => false, 'fehler' => 'Probe mit erfundenen Daten: wird nicht veröffentlicht.']);
}
if (!is_string($d['stand'] ?? null) || !preg_match('/^\d{4}-\d\d-\d\d$/', $d['stand'])) {
    antwort(422, ['ok' => false, 'fehler' => 'Stand fehlt.']);
}
$namen = array_keys($d['dateien']);
if (array_diff($namen, DATEIEN) || array_diff(PFLICHT, $namen)) {
    antwort(422, ['ok' => false, 'fehler' => 'Unerwartete Dateien: ' . implode(', ', $namen)]);
}
// Grobe Sperre vorab (vollständig prüft der tägliche Lauf): keine Felder einzelner Angaben, keine Schlüssel von
// Privatpersonen, keine Kennungen einzelner Angaben
$felder = [];
schluessel($d['dateien'], $felder);
$treffer = array_values(array_intersect(array_keys($felder), VERBOTEN));
if ($treffer) {
    antwort(422, ['ok' => false, 'fehler' => 'Verbotene Felder: ' . implode(', ', $treffer)]);
}
$text = json_encode($d['dateien'], JSON_UNESCAPED_UNICODE);
if (preg_match('/\bV-(\d{3,5}|neu)\b/', $text) || preg_match('/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}/', $text)) {
    antwort(422, ['ok' => false, 'fehler' => 'Einzelangaben oder Schlüssel von Privatpersonen enthalten.']);
}

// Ablegen: erst vollständig schreiben, dann tauschen; die bisherige Fassung wird zu vorher.json
$neu = $ordner . '/.neu.json';
if (file_put_contents($neu, json_encode($d, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), LOCK_EX) === false) {
    antwort(500, ['ok' => false, 'fehler' => 'Speichern gescheitert.']);
}
if (is_file($aktuell) && !rename($aktuell, $vorher)) {
    antwort(500, ['ok' => false, 'fehler' => 'Vorige Fassung nicht sicherbar.']);
}
if (!rename($neu, $aktuell)) {
    antwort(500, ['ok' => false, 'fehler' => 'Speichern gescheitert.']);
}
antwort(200, ['ok' => true, 'aktion' => 'veroeffentlicht', 'stand' => $d['stand'], 'dateien' => $namen, 'vorher' => $stand($vorher)]);
