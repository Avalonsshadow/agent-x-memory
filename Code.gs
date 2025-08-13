function doGet(e){
  try{
    if ((e && e.parameter && e.parameter._method || '').toUpperCase() === 'OPTIONS'){
      return ContentService.createTextOutput('').setMimeType(ContentService.MimeType.TEXT);
    }
    var cmd = (e && e.parameter && e.parameter.cmd || 'meta').toLowerCase();
    if (cmd === 'stats')   return json_({ok:true, stats:getStats_()});
    if (cmd === 'seed')    { ensureStructure_(); return json_({ok:true}); }
    if (cmd === 'scan')    { ensureStructure_(); var r1=walkDrive_(); var r2=buildArchives_(); return json_({ok:true, scan:r1, archives:r2}); }
    if (cmd === 'extract') { var r=tryExtractSmallZips_(); return json_({ok:true, extract:r}); }
    if (cmd === 'kpi_update'){ var s=updateStats_(); return json_({ok:true, stats:s}); }
    if (cmd === 'full_cycle'){
      var t0=Date.now(); ensureStructure_();
      var scan=walkDrive_(), arc=buildArchives_(), ext=tryExtractSmallZips_();
      var stats=updateStats_(); stats.last_runtime_sec = Math.round((Date.now()-t0)/1000);
      return json_({ok:true, scan:scan, arc:arc, ext:ext, stats:stats});
    }
    if (cmd === 'access')  return json_(accessStatus_());
    if (cmd === 'fix')     return json_(fixAccess_(e.parameter.id, e.parameter.mode||'share'));
    // default
    return json_({ok:true, meta:{categories:[], note:'alive'}});
  }catch(err){
    return json_({ok:false, error:String(err)});
  }
}

function json_(obj){
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
README.md
+8
-1

# LCARS Dashboard v3.2

Enthält 12 Module + Drilldowns + Fortschrittsanzeige

Mobilfähig, GitHub-kompatibel.
Mobilfähig, GitHub-kompatibel.

## Deployment Notes

- `const WEBHOOK_URL` in den HTML-Dateien mit der eigenen EXEC-URL der Apps-Script-Web-App füllen.
- Web-App als "Anyone with the link" deployen.
- Brave Shields/Adblocker für das Dashboard deaktivieren.
- HTML nicht direkt per `file://` öffnen – lokalen Server wie VS Code *Live Server* oder `npx serve` nutzen.
