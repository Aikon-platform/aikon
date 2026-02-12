// all of the uppercase variables are passed from Django context and will be defined at runtime.

export const appLang = APP_LANG;  // eslint-disable-line
export const appName = APP_NAME;  // eslint-disable-line
export const webappName = WEBAPP_NAME;  // eslint-disable-line
export const userId = USER_ID;  // eslint-disable-line
export const isSuperuser = IS_SUPERUSER;  // eslint-disable-line
export const csrfToken = CSRF_TOKEN;  // eslint-disable-line
export const modules = ADDITIONAL_MODULES;  // eslint-disable-line
export const regionsType = "Region";
export const appUrl = APP_URL;  // eslint-disable-line
export const aiiinotateUrl = AIIINOTATE_BASE_URL;  // eslint-disable-line
export const miradorUrl = MIRADOR_BASE_URL;  // eslint-disable-line
export const cantaloupeUrl = CANTALOUPE_APP_URL;  // eslint-disable-line
export const mediaPrefix = MEDIA_PATH;  // eslint-disable-line
export const pageSize = PAGE_LEN;  // eslint-disable-line

export const model2title = {
    "Witness": appLang === "en"  ? "Witness" : "Témoin",
    "Work": appLang === "en"  ? "Work" : "Œuvre",
    "Series": appLang === "en"  ? "Series" : "Série d'imprimés",
    "Regions": appLang === "en"  ? "Region Extraction" : "Extraction d'illustrations",
    "User": appLang === "en" ? "User" : "Utilisateur"
}
