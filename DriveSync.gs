/**
 * DriveSync.gs — Google Apps Script
 * ============================================================
 * Script independiente que escanea periódicamente la carpeta
 * "Fireflies Meetings" en busca de PDFs nuevos y los sincroniza
 * con la Nexus Legal API.
 *
 * INSTALACIÓN DEL TRIGGER (una sola vez):
 * ----------------------------------------
 * Opción A — Automática (recomendada):
 *   1. Abre el editor: Extensions → Apps Script
 *   2. Selecciona la función "installTrigger" en el menú desplegable
 *   3. Haz clic en ▶ Run
 *   Esto instala un trigger que ejecuta scanNewPdfs cada 5 minutos.
 *
 * Opción B — Manual desde la UI:
 *   1. Ve a la sección "Triggers" (ícono de reloj en el panel izquierdo)
 *   2. Haz clic en "+ Add Trigger" (esquina inferior derecha)
 *   3. Configura:
 *        - Function to run   : scanNewPdfs
 *        - Deployment        : Head
 *        - Event source      : Time-driven
 *        - Time type         : Minutes timer
 *        - Interval          : Every 5 minutes
 *   4. Guarda. Google pedirá autorización la primera vez.
 *
 * CONFIGURACIÓN (Script Properties):
 * ------------------------------------
 * Agrega estas propiedades en Project Settings → Script Properties:
 *   NEXUS_API_URL      → https://nexus-legal-api-223080314602.us-central1.run.app
 *   DRIVE_SYNC_SECRET  → rOgYIzi9zeJlCDMbv-kiT1poi1zF0jrsEVrGY9lhnzY
 *
 * NOTA: ROOT_FOLDER_ID NO se necesita. El script detecta automáticamente
 * su carpeta padre ("Fireflies Meetings") como carpeta raíz.
 *
 * RENOMBRADO AUTOMÁTICO:
 * Al sincronizar con éxito, el archivo PDF es renombrado a:
 *   <NOMBRE_CLIENTE> - ENVIADO.pdf
 * Los archivos que ya contienen "ENVIADO" en su nombre son ignorados.
 */

// ---------------------------------------------------------------------------
// Script Properties
// ---------------------------------------------------------------------------

function getProps_() {
  return PropertiesService.getScriptProperties();
}

// ---------------------------------------------------------------------------
// Función principal — ejecutada por el trigger de tiempo
// ---------------------------------------------------------------------------

/**
 * Escanea la carpeta del script buscando PDFs nuevos (creados desde la
 * última ejecución) y los envía a la Nexus Legal API.
 *
 * Esta es la función que debe configurarse como trigger de tiempo.
 */
function scanNewPdfs() {
  var scriptFolder = getScriptFolder_();
  if (!scriptFolder) {
    Logger.log('ERROR: No se pudo obtener la carpeta del script.');
    return;
  }

  var props = getProps_();
  var lastRunMs = props.getProperty('LAST_RUN_TIMESTAMP');

  // En la primera ejecución, revisar las últimas 24 horas
  var since = lastRunMs
    ? new Date(parseInt(lastRunMs, 10))
    : new Date(Date.now() - 24 * 60 * 60 * 1000);

  var now = new Date();

  Logger.log(
    'scanNewPdfs: carpeta=' + scriptFolder.getName() +
    ' | desde=' + since.toISOString()
  );

  processNewPdfsInFolder_(scriptFolder, since);

  // Guardar timestamp para la próxima ejecución
  props.setProperty('LAST_RUN_TIMESTAMP', now.getTime().toString());
}

// ---------------------------------------------------------------------------
// Búsqueda y procesamiento de PDFs
// ---------------------------------------------------------------------------

/**
 * Busca PDFs nuevos dentro de una carpeta (y sus subcarpetas) creados
 * después de `since`. Ignora archivos que ya contienen "ENVIADO".
 *
 * @param {GoogleAppsScript.Drive.Folder} folder
 * @param {Date} since - Solo procesar archivos creados después de esta fecha
 */
function processNewPdfsInFolder_(folder, since) {
  // Drive query: PDFs no eliminados creados después del último run
  var sinceIso = since.toISOString();
  var query = 'mimeType = "application/pdf"'
    + ' and trashed = false'
    + ' and createdTime > "' + sinceIso + '"';

  var files = folder.searchFiles(query);

  while (files.hasNext()) {
    var file = files.next();
    var fileName = file.getName();

    // Saltar archivos ya procesados por este script
    if (fileName.toUpperCase().indexOf('ENVIADO') !== -1) {
      Logger.log('scanNewPdfs: ignorado (ya enviado): ' + fileName);
      continue;
    }

    var fileUrl = file.getUrl();
    var folderDate = getParentFolderName_(file);

    Logger.log('scanNewPdfs: procesando — ' + fileName + ' | fecha=' + folderDate);
    callNexusApi_(file, fileName, fileUrl, folderDate);
  }

  // Recorrer subcarpetas recursivamente
  var subfolders = folder.getFolders();
  while (subfolders.hasNext()) {
    processNewPdfsInFolder_(subfolders.next(), since);
  }
}

// ---------------------------------------------------------------------------
// Llamada a la Nexus Legal API
// ---------------------------------------------------------------------------

/**
 * Hace POST a /drive/sync con los metadatos del archivo.
 * Si la sincronización es exitosa, renombra el archivo a:
 *   <nombre_clickup> - ENVIADO.pdf
 *
 * @param {GoogleAppsScript.Drive.File} file
 * @param {string} filenameRaw  - Nombre del archivo (con extensión .pdf)
 * @param {string} fileUrl      - URL de Drive del archivo
 * @param {string} folderDate   - Nombre de la carpeta padre (ej. "2026-03-25")
 */
function callNexusApi_(file, filenameRaw, fileUrl, folderDate) {
  var props = getProps_();
  var apiUrl = props.getProperty('NEXUS_API_URL');
  var secret = props.getProperty('DRIVE_SYNC_SECRET');

  if (!apiUrl || !secret) {
    Logger.log('ERROR: Faltan Script Properties (NEXUS_API_URL o DRIVE_SYNC_SECRET).');
    return;
  }

  var endpoint = apiUrl.replace(/\/$/, '') + '/drive/sync';

  var body = JSON.stringify({
    filename_raw: filenameRaw,
    file_url:     fileUrl,
    folder_date:  folderDate || null
  });

  var options = {
    method:          'post',
    contentType:     'application/json',
    headers:         { Authorization: 'Bearer ' + secret },
    payload:         body,
    muteHttpExceptions: true
  };

  try {
    var response     = UrlFetchApp.fetch(endpoint, options);
    var code         = response.getResponseCode();
    var responseBody = response.getContentText();

    if (code === 200) {
      var data = JSON.parse(responseBody);
      Logger.log(
        'SUCCESS | task_id=' + data.task_id +
        ' | nombre=' + data.nombre_clickup +
        ' | field_updated=' + data.field_updated
      );

      // Renombrar el archivo para indicar que fue enviado por la automatización
      if (data.nombre_clickup) {
        var newName = data.nombre_clickup + ' - ENVIADO.pdf';
        try {
          file.setName(newName);
          Logger.log('RENAMED | ' + filenameRaw + ' → ' + newName);
        } catch (renameErr) {
          Logger.log('WARN | No se pudo renombrar el archivo: ' + renameErr);
        }
      }

    } else if (code === 404) {
      var errData = JSON.parse(responseBody);
      Logger.log(
        'WARN | lead_not_found | query=' + (errData.detail && errData.detail.query) +
        ' | file=' + filenameRaw
      );
    } else {
      Logger.log(
        'ERROR | HTTP ' + code + ' | file=' + filenameRaw +
        ' | response=' + responseBody
      );
    }
  } catch (err) {
    Logger.log('EXCEPTION llamando a Nexus API: ' + err + ' | file=' + filenameRaw);
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Devuelve la carpeta donde está guardado este archivo de Apps Script
 * ("Fireflies Meetings"). No requiere ninguna configuración manual.
 *
 * @returns {GoogleAppsScript.Drive.Folder|null}
 */
function getScriptFolder_() {
  try {
    return DriveApp.getFileById(ScriptApp.getScriptId()).getParents().next();
  } catch (err) {
    Logger.log('WARN | No se pudo obtener la carpeta del script: ' + err);
    return null;
  }
}

/**
 * Devuelve el nombre de la carpeta padre inmediata del archivo.
 * Si el archivo no tiene padre, devuelve null.
 *
 * @param {GoogleAppsScript.Drive.File} file
 * @returns {string|null}
 */
function getParentFolderName_(file) {
  var parents = file.getParents();
  if (parents.hasNext()) {
    return parents.next().getName();
  }
  return null;
}

// ---------------------------------------------------------------------------
// Utilidades de trigger (ejecutar manualmente desde el editor)
// ---------------------------------------------------------------------------

/**
 * Instala el trigger de tiempo programáticamente.
 * Ejecuta esta función UNA SOLA VEZ desde el editor para activar
 * la automatización. Evita duplicar el trigger si ya existe.
 */
function installTrigger() {
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === 'scanNewPdfs') {
      Logger.log('El trigger scanNewPdfs ya está instalado. No se creó uno nuevo.');
      return;
    }
  }

  ScriptApp.newTrigger('scanNewPdfs')
    .timeBased()
    .everyMinutes(5)
    .create();

  Logger.log('Trigger instalado: scanNewPdfs cada 5 minutos.');
}

/**
 * Elimina todos los triggers de scanNewPdfs.
 * Útil para reemplazar el trigger con una configuración nueva.
 */
function removeTrigger() {
  var triggers = ScriptApp.getProjectTriggers();
  var removed = 0;
  for (var i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === 'scanNewPdfs') {
      ScriptApp.deleteTrigger(triggers[i]);
      removed++;
    }
  }
  Logger.log('Triggers eliminados: ' + removed);
}

/**
 * Diagnóstico: muestra el estado del trigger y las Script Properties.
 * Ejecuta desde el editor para verificar la configuración.
 */
function checkStatus() {
  // Triggers
  var triggers = ScriptApp.getProjectTriggers();
  var found = false;
  for (var i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === 'scanNewPdfs') {
      Logger.log('Trigger OK — scanNewPdfs instalado (ID: ' + triggers[i].getUniqueId() + ')');
      found = true;
    }
  }
  if (!found) {
    Logger.log('SIN TRIGGER — Ejecuta installTrigger() para activarlo.');
  }

  // Script Properties
  var props = getProps_();
  Logger.log('NEXUS_API_URL     = ' + (props.getProperty('NEXUS_API_URL')     || '(no definida)'));
  Logger.log('DRIVE_SYNC_SECRET = ' + (props.getProperty('DRIVE_SYNC_SECRET') ? '***' : '(no definida)'));
  Logger.log('LAST_RUN          = ' + (props.getProperty('LAST_RUN_TIMESTAMP')
    ? new Date(parseInt(props.getProperty('LAST_RUN_TIMESTAMP'), 10)).toISOString()
    : '(nunca ejecutado)'));

  // Carpeta del script
  var folder = getScriptFolder_();
  Logger.log('Carpeta script    = ' + (folder ? folder.getName() + ' (' + folder.getId() + ')' : 'ERROR'));
}
