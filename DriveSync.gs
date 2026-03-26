/**
 * DriveSync.gs — Google Apps Script
 * ============================================================
 * Trigger de Google Drive que detecta PDFs nuevos en la carpeta
 * "Fireflies Meetings" y los sincroniza con la Nexus Legal API.
 *
 * INSTALACIÓN DEL TRIGGER (una sola vez por proyecto):
 * -----------------------------------------------------
 * 1. Abre el editor: Extensions → Apps Script
 * 2. Ve a la sección "Triggers" (ícono de reloj en el panel izquierdo)
 * 3. Haz clic en "+ Add Trigger" (esquina inferior derecha)
 * 4. Configura:
 *      - Function to run   : onDriveChange
 *      - Deployment        : Head
 *      - Event source      : From Google Drive
 *      - Event type        : On change
 * 5. Guarda. Google pedirá autorización la primera vez.
 *
 * CONFIGURACIÓN (Script Properties):
 * ------------------------------------
 * Agrega estas propiedades en Project Settings → Script Properties:
 *   NEXUS_API_URL      → URL base de Nexus Legal API en Cloud Run
 *                        ej. https://nexus-legal-api-xxxx-uc.a.run.app
 *   DRIVE_SYNC_SECRET  → El mismo token configurado en DRIVE_SYNC_SECRET
 *                        de la API (sin el prefijo "Bearer")
 *   ROOT_FOLDER_ID     → ID de la carpeta "Fireflies Meetings" en Drive
 *                        (parte de la URL: drive.google.com/drive/folders/<ID>)
 */

// ---------------------------------------------------------------------------
// Constantes de configuración (leídas de Script Properties)
// ---------------------------------------------------------------------------

/**
 * Devuelve las propiedades del script.
 * @returns {GoogleAppsScript.Properties.Properties}
 */
function getProps_() {
  return PropertiesService.getScriptProperties();
}

// ---------------------------------------------------------------------------
// Handler principal del trigger onChange
// ---------------------------------------------------------------------------

/**
 * Punto de entrada del trigger onChange de Google Drive.
 * Se ejecuta automáticamente cuando hay cambios en Drive.
 *
 * @param {GoogleAppsScript.Drive.Schema.Change} e - Evento de cambio de Drive
 */
function onDriveChange(e) {
  // Solo procesar eventos de tipo ADDED
  if (!e || e.changeType !== 'ADDED') {
    return;
  }

  var fileId = e.fileId;
  if (!fileId) {
    Logger.log('onDriveChange: evento sin fileId, ignorado.');
    return;
  }

  var file;
  try {
    file = DriveApp.getFileById(fileId);
  } catch (err) {
    Logger.log('onDriveChange: no se pudo acceder al archivo ' + fileId + ': ' + err);
    return;
  }

  // Filtrar solo PDFs
  var mimeType = file.getMimeType();
  var fileName = file.getName();

  var isPdf =
    mimeType === 'application/pdf' ||
    fileName.toLowerCase().endsWith('.pdf');

  if (!isPdf) {
    Logger.log('onDriveChange: archivo ignorado (no es PDF): ' + fileName);
    return;
  }

  // Verificar que el archivo está dentro de la carpeta raíz configurada
  var rootFolderId = getProps_().getProperty('ROOT_FOLDER_ID');
  if (rootFolderId && !isInsideFolder_(file, rootFolderId)) {
    Logger.log('onDriveChange: PDF fuera de la carpeta raíz, ignorado: ' + fileName);
    return;
  }

  // Obtener metadatos
  var filenameRaw = stripPdfExtension_(fileName);
  var fileUrl = file.getUrl();
  var folderDate = getParentFolderName_(file);

  Logger.log('onDriveChange: procesando PDF — ' + filenameRaw + ' | ' + folderDate);

  // Llamar a la API
  callNexusApi_(filenameRaw, fileUrl, folderDate);
}

// ---------------------------------------------------------------------------
// Llamada a la Nexus Legal API
// ---------------------------------------------------------------------------

/**
 * Hace POST a /drive/sync con los metadatos del archivo.
 *
 * @param {string} filenameRaw  - Nombre del archivo sin extensión
 * @param {string} fileUrl      - URL de Drive del archivo
 * @param {string} folderDate   - Nombre de la carpeta padre (ej. "2026-03-25")
 */
function callNexusApi_(filenameRaw, fileUrl, folderDate) {
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
    file_url: fileUrl,
    folder_date: folderDate || null
  });

  var options = {
    method: 'post',
    contentType: 'application/json',
    headers: {
      Authorization: 'Bearer ' + secret
    },
    payload: body,
    muteHttpExceptions: true  // Para poder leer el body en caso de error
  };

  try {
    var response = UrlFetchApp.fetch(endpoint, options);
    var code = response.getResponseCode();
    var responseBody = response.getContentText();

    if (code === 200) {
      var data = JSON.parse(responseBody);
      Logger.log(
        'SUCCESS | task_id=' + data.task_id +
        ' | nombre=' + data.nombre_clickup +
        ' | field_updated=' + data.field_updated
      );
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
 * Elimina la extensión .pdf (case-insensitive) del nombre del archivo.
 *
 * @param {string} name - Nombre completo del archivo
 * @returns {string}
 */
function stripPdfExtension_(name) {
  return name.replace(/\.pdf$/i, '');
}

/**
 * Devuelve el nombre de la carpeta padre inmediata del archivo.
 * Si el archivo no tiene padre (carpeta raíz de Drive), devuelve null.
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

/**
 * Comprueba recursivamente si un archivo está dentro de la carpeta
 * con el ID dado. Evita procesar PDFs de otras partes de Drive.
 *
 * @param {GoogleAppsScript.Drive.File} file
 * @param {string} folderId - ID de la carpeta raíz objetivo
 * @returns {boolean}
 */
function isInsideFolder_(file, folderId) {
  var parents = file.getParents();
  while (parents.hasNext()) {
    var parent = parents.next();
    if (parent.getId() === folderId) {
      return true;
    }
    // Buscar un nivel más arriba (hasta raíz de Drive)
    if (isInsideFolder_(DriveApp.getFolderById(parent.getId()), folderId)) {
      return true;
    }
  }
  return false;
}

// ---------------------------------------------------------------------------
// Utilidad: instalar el trigger programáticamente (ejecución manual)
// ---------------------------------------------------------------------------

/**
 * Verifica si el trigger onChange ya está instalado y lo reporta.
 * Ejecuta esta función desde el editor para diagnóstico.
 *
 * NOTA: Los triggers de tipo "On change" (Drive) SOLO se pueden instalar
 * desde la UI de Apps Script — no existe API programática para crearlos.
 * Sigue las instrucciones al inicio del archivo.
 */
function checkTrigger() {
  var triggers = ScriptApp.getProjectTriggers();
  var found = false;
  for (var i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === 'onDriveChange') {
      Logger.log('✅ Trigger onDriveChange está instalado (ID: ' + triggers[i].getUniqueId() + ')');
      found = true;
    }
  }
  if (!found) {
    Logger.log('⚠️  Trigger onDriveChange NO está instalado. Instálalo desde la UI de Triggers.');
  }
}
