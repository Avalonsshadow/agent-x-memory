/***** CONFIG **********************************************************/
const ROOT_NAME     = 'AgentX_Ablage';          // Drive-Root
const DASHBOARD_DIR = 'AgentX_Dashboards';      // meta.json + Backups
const SHEET_URL     = 'https://docs.google.com/spreadsheets/d/1NK6B8s-MQp38ZvMfsN2dAH0KHXDcfzdeXTYG7t4mfXQ/edit';
const SHEET_TAB     = 'Modules';                // Haupt-Tabelle für Module
/***********************************************************************/

/**
 * API:
 *  ?cmd=alive
 *  ?cmd=list
 *  ?cmd=meta
 *  ?cmd=seed
 *  ?cmd=sheet_bootstrap
 *  ?cmd=sheet_import
 *  ?cmd=sheet_export
 *  ?cmd=kpi_update
 *  ?cmd=csv_import
 *  ?cmd=full_cycle
 */
function doGet(e) {
  const cmd = String(e && e.parameter && e.parameter.cmd || 'alive').toLowerCase();
  try {
    if (cmd === 'alive') return json_({ ok:true, msg:'alive' });

    if (cmd === 'list') {
      const root = getOrCreateFolderByPath_(ROOT_NAME);
      const items = listFolders_(root).map(f => ({ name:f.getName() }));
      return json_({ ok:true, path:ROOT_NAME, items });
    }

    if (cmd === 'meta') {
      const m = readMeta_();
      // Dashboard versteht beides: meta + flat categories
      return json_({ ok:true, meta:m, categories:(m.categories||[]) });
    }

    if (cmd === 'sheet_bootstrap') {
      ensureSheetStructure_();
      const root = getOrCreateFolderByPath_(ROOT_NAME);
      const folders = listFolders_(root).map(f => f.getName());
      bootstrapSheet_(folders);
      return json_({ ok:true, msg:'sheet_bootstrap_ok', rows:folders.length });
    }

    if (cmd === 'seed') {
      const root = getOrCreateFolderByPath_(ROOT_NAME);
      const modules = readSheetModules_();
      const categories = generateCategories_(modules, root);
      writeMeta_(categories);
      return json_({ ok:true, msg:'seeded', count:categories.length, categories });
    }

    if (cmd === 'sheet_import') {
      const root = getOrCreateFolderByPath_(ROOT_NAME);
      const modules = readSheetModules_();
      const categories = generateCategories_(modules, root);
      writeMeta_(categories);
      return json_({ ok:true, msg:'sheet_import_ok', count:categories.length });
    }

    if (cmd === 'sheet_export') {
      const meta = readMeta_();
      exportMetaToSheet_(meta);
      return json_({ ok:true, msg:'sheet_export_ok', count:(meta.categories||[]).length });
    }

    if (cmd === 'kpi_update') {
      const info = updateKpis_();
      return json_({ ok:true, msg:'kpi_updated', info });
    }

    if (cmd === 'csv_import') {
      const stats = importCsvFromDrive_();
      return json_({ ok:true, msg:'csv_import_ok', stats });
    }

    if (cmd === 'full_cycle') {
      // 1) Struktur sicherstellen
      ensureSheetStructure_();
      // 2) CSV importieren
      const stats = importCsvFromDrive_();
      // 3) KPI berechnen
      const kpi = updateKpis_();
      // 4) meta.json neu schreiben
      const root = getOrCreateFolderByPath_(ROOT_NAME);
      const modules = readSheetModules_();
      const categories = generateCategories_(modules, root);
      writeMeta_(categories);
      return json_({ ok:true, msg:'full_cycle_ok', stats, kpi, count:categories.length });
    }

    return json_({ ok:false, error:'unknown_cmd: '+cmd });
  } catch (err) {
    return json_({ ok:false, error:String(err) });
  }
}

/* ---------------------------- DRIVE -------------------------------- */

function getOrCreateFolderByPath_(path) {
  const parts = String(path).split('/').filter(Boolean);
  let cur = DriveApp.getRootFolder();
  for (const p of parts) {
    const it = cur.getFoldersByName(p);
    cur = it.hasNext() ? it.next() : cur.createFolder(p);
  }
  return cur;
}
function listFolders_(folder) {
  const out = [];
  const it = folder.getFolders();
  while (it.hasNext()) out.push(it.next());
  return out;
}

/* ---------------------------- META --------------------------------- */
/* MIME-Fix: nur Blobs mit 'application/json' erstellen */

function metaFile_(createIfMissing = true) {
  const dash = getOrCreateFolderByPath_(ROOT_NAME + '/' + DASHBOARD_DIR);
  let it = dash.getFilesByName('meta.json');
  if (it.hasNext()) return it.next();
  if (!createIfMissing) throw new Error('meta.json not found');
  const payload = JSON.stringify({ version:'2.0', generated:new Date(), categories:[] }, null, 2);
  return dash.createFile(Utilities.newBlob(payload, 'application/json', 'meta.json'));
}
function readMeta_() {
  const f = metaFile_(true);
  const txt = f.getBlob().getDataAsString('UTF-8');
  try { return JSON.parse(txt || '{}'); }
  catch { return { version:'2.0', categories:[] }; }
}
function writeMeta_(categories) {
  const dash = getOrCreateFolderByPath_(ROOT_NAME + '/' + DASHBOARD_DIR);
  const stamp = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd'_'HH-mm-ss");

  // Backup
  const backupPayload = JSON.stringify({ version:'2.0', generated:new Date(), categories }, null, 2);
  dash.createFile(Utilities.newBlob(backupPayload, 'application/json', `meta_${stamp}.json`));

  // Replace meta.json
  const it = dash.getFilesByName('meta.json');
  if (it.hasNext()) it.next().setTrashed(true);
  const metaPayload = JSON.stringify({ version:'2.0', generated:new Date(), categories }, null, 2);
  dash.createFile(Utilities.newBlob(metaPayload, 'application/json', 'meta.json'));
}

/* ---------------------------- SHEET -------------------------------- */

function openSheet_() {
  const ss = SpreadsheetApp.openByUrl(SHEET_URL);
  let sh = ss.getSheetByName(SHEET_TAB);
  if (!sh) sh = ss.insertSheet(SHEET_TAB);
  return sh;
}

// Pflicht-/Empfehlungs-Spalten in "Modules"
const COLS = ['Folder','Title','Progress','Status','Access','Stops','Actions','Notes','Icon','Accent',
              'Priority','BlockerRate','DoneRate','LeadTime','UpdatedAt','History'];

function ensureSheetStructure_() {
  const ss = SpreadsheetApp.openByUrl(SHEET_URL);

  // Modules
  let mod = ss.getSheetByName('Modules');
  if (!mod) mod = ss.insertSheet('Modules');
  // Kopfzeile sicherstellen
  const have = mod.getRange(1,1,1,Math.max(mod.getLastColumn(),1)).getValues()[0].map(h=>String(h||'').trim()).filter(Boolean);
  let changed = false;
  COLS.forEach(c=>{ if(have.indexOf(c)===-1) changed = true; });
  if (changed) { mod.clear(); mod.getRange(1,1,1,COLS.length).setValues([COLS]); }

  // Extra-Tabs für spätere Auswertungen/Projekte
  [['KPI', ['Date','Module','Progress','BlockerRate','DoneRate','LeadTime']],
   ['KPI_History', ['ts','module','progress','status','note']],
   ['Projects', ['ID','Module','Title','Status','Priority','Owner','Start','Due','Progress','Tags','Notes']],
   ['Tasks', ['ID','ProjectID','Title','Status','Owner','Start','Due','Note']]
  ].forEach(([name,head])=>{
     if (!ss.getSheetByName(name)) {
       const sh = ss.insertSheet(name);
       sh.getRange(1,1,1,head.length).setValues([head]);
     }
  });
}

function bootstrapSheet_(folderNames) {
  const sh = openSheet_();
  sh.clear();
  sh.getRange(1,1,1,COLS.length).setValues([COLS]);
  const rows = folderNames.map(name => ([
    name, guessTitle_(name), 25, 'start', 'privat • aktiv (lokal)',
    'keine', '', '', '', '',
    'P3', 0, 0, 0, new Date(), JSON.stringify([{ts:new Date(), ev:'bootstrap'}])
  ]));
  if (rows.length) sh.getRange(2,1,rows.length,COLS.length).setValues(rows);
  sh.autoResizeColumns(1, COLS.length);
}

function readSheetModules_() {
  const sh = openSheet_();
  const lastRow = sh.getLastRow();
  if (lastRow < 2) return [];
  const head = sh.getRange(1,1,1,sh.getLastColumn()).getValues()[0].map(h=>String(h||'').trim());
  const idx = colIndex_(head);
  const rg  = sh.getRange(2,1,lastRow-1,sh.getLastColumn()).getValues();

  const out = [];
  for (let r=0; r<rg.length; r++) {
    const row = rg[r];
    const folder = getCell_(row, idx.Folder);
    if (!folder) continue;
    out.push({
      folder,
      title:   getCell_(row, idx.Title)   || guessTitle_(folder),
      progress:numClamp_(getCell_(row, idx.Progress), 0, 100, 25),
      status:  (getCell_(row, idx.Status) || 'start').toLowerCase(),
      access:  getCell_(row, idx.Access)  || 'privat • aktiv (lokal)',
      stops:   listFromCell_(getCell_(row, idx.Stops)),
      actions: listFromCell_(getCell_(row, idx.Actions)),
      notes:   getCell_(row, idx.Notes)   || '',
      icon:    getCell_(row, idx.Icon)    || '',
      accent:  getCell_(row, idx.Accent)  || ''
    });
  }
  return out;
}

function exportMetaToSheet_(meta) {
  const sh = openSheet_();
  sh.clear();
  sh.getRange(1,1,1,COLS.length).setValues([COLS]);
  const cats = (meta && meta.categories) || [];
  const rows = cats.map(c => ([
    c.folder, c.title || guessTitle_(c.folder), Number(c.progress||0), c.status || 'start',
    c.access || 'privat • aktiv (lokal)', (c.stops||[]).join('; '), (c.actions||[]).join('; '),
    c.notes || '', c.icon || '', c.accent || '',
    'P3', 0, 0, 0, new Date(), JSON.stringify([{ts:new Date(), ev:'export'}])
  ]));
  if (rows.length) sh.getRange(2,1,rows.length,COLS.length).setValues(rows);
  sh.autoResizeColumns(1, COLS.length);
}

/* ---------- CSV IMPORT (Drive → Sheets) ----------------------------- */
/* Importiert alle *.csv unter ROOT_NAME (auch Unterordner).            */
/* Mappt bekannte Dateien auf bekannte Tabs (Projects, Tasks, KPI etc.) */

function importCsvFromDrive_() {
  const root = getOrCreateFolderByPath_(ROOT_NAME);
  const files = listCsvFilesRecursive_(root);
  const ss = SpreadsheetApp.openByUrl(SHEET_URL);

  const stats = { scanned:files.length, imported:0, tabs:[] };

  files.forEach(f=>{
    const name = String(f.getName()||'').trim();
    const base = name.replace(/\.csv$/i,'');
    const csv  = f.getBlob().getDataAsString('UTF-8');
    const rows = Utilities.parseCsv(csv);

    // Zieltab bestimmen
    let tab = null;
    if (/project/i.test(base)) tab = 'Projects';
    else if (/task/i.test(base)) tab = 'Tasks';
    else if (/kpi/i.test(base)) tab = 'KPI';
    else if (/econom/i.test(base)) tab = 'Economics';
    else tab = base.substring(0,96); // generisch

    let sh = ss.getSheetByName(tab);
    if (!sh) sh = ss.insertSheet(tab);

    // Clear + write
    sh.clear();
    if (rows && rows.length) {
      sh.getRange(1,1,rows.length, rows[0].length).setValues(rows);
      stats.imported++; stats.tabs.push(tab);
    }
  });

  return stats;
}
function listCsvFilesRecursive_(folder) {
  let results = [];
  // Dateien in diesem Ordner
  let it = folder.getFiles();
  while (it.hasNext()) {
    const f = it.next();
    if (String(f.getName()).toLowerCase().endsWith('.csv')) results.push(f);
  }
  // Unterordner
  let ft = folder.getFolders();
  while (ft.hasNext()) {
    results = results.concat(listCsvFilesRecursive_(ft.next()));
  }
  return results;
}

/* ------------------------- KPI UPDATE ------------------------------- */

function updateKpis_() {
  ensureSheetStructure_();
  const ss = SpreadsheetApp.openByUrl(SHEET_URL);
  const shM = ss.getSheetByName('Modules');
  const shP = ss.getSheetByName('Projects');
  const shT = ss.getSheetByName('Tasks');

  const m = shM.getDataRange().getValues();
  if (m.length < 2) return { updated:0 };

  const head = m[0]; const idx = colIndex_(head);

  const p = (shP && shP.getLastRow()>1) ? shP.getDataRange().getValues().slice(1) : [];
  const t = (shT && shT.getLastRow()>1) ? shT.getDataRange().getValues().slice(1) : [];

  const tasksByProject = {};
  t.forEach(row=>{
    const pid = String(row[1]||'').trim();
    if (!tasksByProject[pid]) tasksByProject[pid]=[];
    tasksByProject[pid].push(row);
  });

  // Projects: Spalte 0=ID, 1=Module
  const projectsByFolder = {};
  p.forEach(row=>{
    const folder = String(row[1]||'').trim();
    if (!folder) return;
    if (!projectsByFolder[folder]) projectsByFolder[folder]=[];
    projectsByFolder[folder].push(row);
  });

  let updated = 0;
  for (let r=1; r<m.length; r++) {
    const row = m[r];
    const folder = getCell_(row, idx.Folder);
    if (!folder) continue;

    const myProjects = projectsByFolder[folder] || [];
    let totalTasks=0, blockedTasks=0, doneTasks=0, leadCount=0, leadSum=0;

    myProjects.forEach(pr=>{
      const pid = String(pr[0]||'').trim();
      const myTasks = tasksByProject[pid] || [];
      myTasks.forEach(tk=>{
        totalTasks++;
        const st = String(tk[3]||'').toLowerCase();
        if (st==='blocked' || st==='blocker') blockedTasks++;
        if (st==='done') doneTasks++;
        const s = parseDate_(tk[5]); const d = parseDate_(tk[6]);
        if (s && d) { leadSum += Math.max(0,(d-s)/(1000*60*60*24)); leadCount++; }
      });
    });

    const blockerRate = totalTasks ? Math.round(blockedTasks/totalTasks*100) : 0;
    const doneRate    = totalTasks ? Math.round(doneTasks/totalTasks*100)   : 0;
    const leadTime    = leadCount ? Math.round(leadSum/leadCount)           : 0;

    setCell_(m, r, idx.BlockerRate, blockerRate);
    setCell_(m, r, idx.DoneRate,    doneRate);
    setCell_(m, r, idx.LeadTime,    leadTime);
    setCell_(m, r, idx.UpdatedAt,   new Date());

    try {
      const htxt = getCell_(m[r], idx.History) || '[]';
      const hist = JSON.parse(htxt);
      hist.push({ ts:new Date(), ev:'kpi_update', data:{ blocked:blockedTasks, total:totalTasks, done:doneTasks }});
      setCell_(m, r, idx.History, JSON.stringify(hist));
    } catch(_) {
      setCell_(m, r, idx.History, JSON.stringify([{ ts:new Date(), ev:'kpi_update' }]));
    }
    updated++;
  }

  shM.getRange(1,1,m.length,m[0].length).setValues(m);
  return { updated };
}

/* ------------------------------ UTIL -------------------------------- */

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
function colIndex_(head) {
  const map = {};
  COLS.forEach(c => map[c] = head.indexOf(c));
  return map;
}
function getCell_(row, i) { return i>=0 ? (row[i] ?? '') : ''; }
function setCell_(matrix, r, i, v){ if(i>=0){ matrix[r][i]=v; } }
function numClamp_(v, min, max, fallback) {
  const n = Number(String(v).replace('%','').trim());
  return isFinite(n) ? Math.max(min, Math.min(max, n)) : fallback;
}
function listFromCell_(v){ if (v==null) return []; return String(v).split(/[;,]/).map(s=>s.trim()).filter(Boolean); }
function guessTitle_(folder){ return String(folder||'').replace(/[_\-]+/g,' ').replace(/\s+/g,' ').trim(); }
function slug_(s){ return String(s||'').toLowerCase().replace(/\s+/g,'_').replace(/[^a-z0-9_]/g,''); }
function normStatus_(s){ const v=String(s||'start').toLowerCase(); return (v==='ok'||v==='block'||v==='start')?v:'start'; }
function parseDate_(v){ if(!v) return null; try{ return new Date(v); }catch(_){ return null; } }
