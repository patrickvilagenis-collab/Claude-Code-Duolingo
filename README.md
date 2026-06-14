# Asistente Pro

App de escritorio **portable** que lee tu **correo y calendario de Microsoft 365**
y usa **Claude (IA)** para resumir correos, generar **actas de reunión (MoM)**,
extraer tareas y **planificarte** el día o la semana. Incluye un **gestor de
tareas** local.

- 🖥️ Interfaz gráfica con pestañas (Bandeja, Calendario, Tareas, Actas, Planificador, Ajustes)
- 📧 Microsoft 365 vía **Microsoft Graph** (solo lectura de correo y calendario)
- 🧠 IA con **Claude API** (`claude-opus-4-8` por defecto, configurable)
- ✅ Gestor de tareas en SQLite local
- 📦 Se empaqueta en un único **`.exe` portable** (Windows)

---

## ⚡ Resumen rápido (3 pasos)

1. **Registra una app en Azure** (5 min) → obtienes un **Client ID**.
2. **Consigue una API key de Anthropic** → en https://console.anthropic.com
3. **Genera el `.exe`** con `build.bat`, ábrelo, pega ambas claves en **Ajustes** e inicia sesión.

> ⚠️ La compilación del `.exe` se hace **en tu PC con Windows** (este repo no
> incluye el binario). Tus credenciales nunca se guardan en el repositorio:
> viven solo en la carpeta `data/` junto al ejecutable.

---

## 1. Requisitos

- **Windows 10/11** (para el `.exe`). En desarrollo también funciona en Linux/Mac.
- **Python 3.10 o superior** (solo para construir/desarrollar): https://www.python.org/downloads/
  - Marca *"Add Python to PATH"* durante la instalación.

---

## 2. Registrar la app en Azure AD (para leer correo/calendario)

Microsoft exige registrar una "aplicación" para acceder a tu correo corporativo.
Es gratis y se hace una vez.

1. Entra en el **Portal de Azure**: https://portal.azure.com
2. Busca **"Microsoft Entra ID"** (antes Azure Active Directory).
3. Menú **App registrations → New registration**.
   - **Name**: `Asistente Pro` (o lo que quieras).
   - **Supported account types**: *Accounts in this organizational directory only*
     (o *Accounts in any organizational directory* si tu IT lo permite).
   - **Redirect URI**: déjalo vacío.
   - Pulsa **Register**.
4. En la página de la app, copia el **Application (client) ID** → este es tu **Client ID**.
   Copia también el **Directory (tenant) ID** si tu empresa requiere fijar el tenant.
5. Menú **Authentication**:
   - Baja a **Advanced settings → Allow public client flows** → ponlo en **Yes**.
   - **Save**.
6. Menú **API permissions → Add a permission → Microsoft Graph → Delegated permissions**.
   Añade: **`User.Read`**, **`Mail.Read`**, **`Calendars.Read`**.
   - Si aparece *"Grant admin consent"* y tienes permisos, púlsalo. Si no, tu
     primer inicio de sesión pedirá el consentimiento (o el de tu administrador).

> 🏢 **Nota corporativa:** algunas empresas bloquean el registro de apps o exigen
> aprobación del administrador de IT. Si el inicio de sesión falla por "necesita
> aprobación del administrador", contacta con tu IT y enséñales esta página: solo
> se piden permisos de **lectura** de correo y calendario.

---

## 3. Conseguir la API key de Anthropic (Claude)

1. Entra en https://console.anthropic.com
2. **Settings → API Keys → Create Key**.
3. Copia la clave (`sk-ant-...`). La pegarás en **Ajustes** dentro de la app.

> El uso de la IA tiene coste por tokens. Por defecto se usa `claude-opus-4-8`
> (el más capaz). Para abaratar, en Ajustes puedes elegir `claude-sonnet-4-6`
> o `claude-haiku-4-5`.

---

## 4. Construir el `.exe` portable

En la carpeta del proyecto, abre **CMD** o **PowerShell** y ejecuta:

```bat
build.bat
```

Esto crea un entorno virtual, instala dependencias y genera:

```
dist\AsistentePro.exe
```

Copia ese **único archivo** a cualquier PC con Windows y ejecútalo (doble clic).
La primera vez creará una carpeta `data\` a su lado para guardar tu configuración,
la sesión y la base de datos de tareas.

---

## 5. Ejecutar en modo desarrollo (opcional)

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
python run.py
```

---

## 6. Primer uso

1. Abre la app → pestaña **⚙ Ajustes**.
2. Pega el **Client ID** (y Tenant si aplica) y la **API Key de Anthropic**. Pulsa **Guardar**.
3. Pulsa **🔐 Iniciar sesión**: aparecerá un **código**. Ábrelo en el navegador
   (`microsoft.com/devicelogin`), introduce el código y autentícate con tu cuenta
   corporativa. La sesión queda recordada.
4. Ya puedes:
   - **📥 Bandeja**: ver correos, **Resumir** con IA, **Extraer tareas**.
   - **📅 Calendario**: ver próximos eventos, crear tareas de preparación.
   - **✅ Tareas**: gestor con prioridad, fecha y estado.
   - **📝 Actas (MoM)**: pega notas → genera el acta, guárdala/expórtala, extrae tareas.
   - **🗓 Planificador**: combina calendario + tareas y te propone un plan.

---

## Configurar con variables de entorno (alternativa)

Para no escribir secretos en disco, puedes definir antes de abrir la app:

| Variable             | Uso                          |
|----------------------|------------------------------|
| `ANTHROPIC_API_KEY`  | API key de Claude            |
| `AZURE_CLIENT_ID`    | Client ID de Azure           |
| `AZURE_TENANT_ID`    | Tenant ID (o `common`)       |

Tienen prioridad sobre `data/config.json`.

---

## Privacidad y datos

- Todo es **local**: configuración, token y tareas viven en `data/` junto al `.exe`.
- El correo/calendario se consulta directamente a **Microsoft Graph** con tu sesión.
- Al usar la IA, el **contenido del correo/notas que resumes se envía a la API de
  Anthropic** para procesarlo. No uses la función de IA sobre información que tu
  empresa no permita enviar a servicios externos.
- Para borrar todo: cierra la app y elimina la carpeta `data/`.

---

## Estructura del proyecto

```
run.py                 Punto de entrada
build.bat              Genera el .exe portable
requirements.txt       Dependencias
config.example.json    Ejemplo de configuración
src/
  main.py              Arranque
  paths.py             Rutas portables (data/)
  config.py            Configuración
  storage.py           SQLite (tareas y actas)
  graph_client.py      Microsoft Graph (auth + correo + calendario)
  ai_client.py         Claude (resumen, MoM, planificación)
  ui/                  Interfaz (pestañas)
```

---

## Resolución de problemas

- **"No se pudo iniciar el flujo de autenticación"** → revisa el Client ID y que
  *Allow public client flows* esté en **Yes** en Azure.
- **"Necesita aprobación del administrador"** → tu IT debe conceder el consentimiento
  a los permisos `Mail.Read` / `Calendars.Read`.
- **"Sesión caducada"** → ve a Ajustes y vuelve a **Iniciar sesión**.
- **Error de IA / 401** → revisa la API Key de Anthropic en Ajustes.
- **El antivirus marca el `.exe`** → es común con apps de PyInstaller sin firmar;
  añádelo a excepciones o ejecútalo en modo desarrollo.
