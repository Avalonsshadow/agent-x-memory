
function doPost(e) {
  try {
    var folder = DriveApp.getFolderById("1kHnPwubTDTfO4oFUjj1AOKmv8_itpuj7");
    var blob = e.parameter.file ? Utilities.newBlob(Utilities.base64Decode(e.parameter.file), e.parameter.mimeType, e.parameter.filename) : null;
    if (blob) {
      folder.createFile(blob);
      return ContentService.createTextOutput("✅ Upload erfolgreich.");
    } else {
      return ContentService.createTextOutput("⚠️ Kein Blob gefunden.");
    }
  } catch (err) {
    return ContentService.createTextOutput("❌ Fehler: " + err);
  }
}
