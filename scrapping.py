import os  
import time  
import sys  
from selenium import webdriver  
from selenium.webdriver.common.by import By  
from selenium.webdriver.chrome.service import Service  
from selenium.webdriver.support.ui import WebDriverWait  
from selenium.webdriver.support import expected_conditions as EC  
from selenium.webdriver.common.action_chains import ActionChains  

DRIVER_ROOT = 'c:/Users/jose5/OneDrive/Documentos/chromedriver.exe'  
CORREO = 'al049738@uacam.mx'  
CONTRASENIA = 'DSA22093'  
COORDINACION_FOLDER = 'SEGUIMIENTO DE DATOS DE EXCAVACIÓN'  
FOLIO = 'EXC-01'  
CURRENT_HDD = 'Tramo 2' # Dejar vacío si no aplica  
LOCAL_ROOT = 'E:/EXC-01/Tramo 2'  

def is_hidden(file_path):  
    """  
    Verifica si un archivo o carpeta es oculto o comienza con punto.  
    """  
    basename = os.path.basename(file_path)  

    # Verificar si el nombre comienza con punto  
    if basename.startswith('.'):  
        return True  

    # Verificar atributos de archivo oculto en Windows  
    if os.name == 'nt':  
        import ctypes  
        try:  
            attrs = ctypes.windll.kernel32.GetFileAttributesW(file_path)  
            return attrs != -1 and bool(attrs & 2)  # FILE_ATTRIBUTE_HIDDEN  
        except:  
            return False  

    return False  

def handle_confirmation(driver):  
    try:  
        alert = WebDriverWait(driver, 2).until(EC.alert_is_present())  
        alert.accept()  
        print("Confirmación aceptada automáticamente.")  
    except:  
        pass  

def ensure_folder_suffix(url):  
    """  
    Asegura que la URL termina con /* para indicar que es la carpeta actual.  
    """  
    if not url.endswith("/*"):  
        return f"{url}/*"  
    return url  

def scroll_to_element(driver, element):  
    """  
    Desplaza la página hasta que el elemento sea visible.  
    """  
    try:  
        driver.execute_script("arguments[0].scrollIntoView(true);", element)  
        time.sleep(1)  
    except Exception as e:  
        print(f"Error al desplazar hacia el elemento: {e}")  

def click_with_js(driver, element):  
    """  
    Realiza clic en un elemento utilizando JavaScript.  
    """  
    try:  
        driver.execute_script("arguments[0].click();", element)  
    except Exception as e:  
        print(f"Error al hacer clic en el elemento con JavaScript: {e}")  

def create_remote_folder(driver, folder_name):  
    try:  
        print(f"Creando carpeta: {folder_name}")  
        folder_input = WebDriverWait(driver, 10).until(  
            EC.presence_of_element_located((By.ID, "nombre_carpeta"))  
        )  
        folder_input.clear()  
        folder_input.send_keys(folder_name)  

        create_button = driver.find_element(By.CSS_SELECTOR, "a.btn-success")  

        # Asegúrate de que el botón sea visible  
        scroll_to_element(driver, create_button)  

        # Intentar hacer clic con JavaScript si es necesario  
        click_with_js(driver, create_button)  

        handle_confirmation(driver)  

        WebDriverWait(driver, 10).until(  
            EC.presence_of_element_located((By.LINK_TEXT, folder_name))  
        )  
        print(f"Carpeta '{folder_name}' creada exitosamente.")  
    except Exception as e:  
        print(f"Error al crear la carpeta '{folder_name}': {e}")  
        print("Finalizando el programa debido a un error crítico.")  
        sys.exit(1)  

def verify_file(driver, file_path):  
    try:  
        filename = os.path.basename(file_path)  
        print(f'Filename: {filename}')  

        possible_filenames = [filename, f"*{filename}"]  

        for name in possible_filenames:  
            try:  
                file = driver.find_elements(By.LINK_TEXT, name)  
                if len(file) > 0:  
                    print(f'Encontrado: {file}')  
                    return True  
            except:  
                continue  

        print(f'No se encontró ninguna variante del archivo {filename}')  
        return False  

    except Exception as e:  
        print(f'Error al encontrar el link: {e}')  
        return False  

def upload_file(driver, file_path):  
    try:  
        if is_hidden(file_path):  # Ignorar archivos ocultos  
            print(f"Ignorando archivo oculto: {file_path}")  
            return  

        exist_file = verify_file(driver, file_path)  
        if exist_file:  
            return  

        print(f"Subiendo archivo: {file_path}")  
        file_input = WebDriverWait(driver, 10).until(  
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))  
        )  
        file_input.send_keys(file_path)  

        wait_for_all_uploads(driver)  
        print(f"Archivo '{file_path}' subido exitosamente.")  
    except Exception as e:  
        print(f"Error al subir el archivo '{file_path}': {e}")  

def wait_for_all_uploads(driver, max_wait=18000):  
    print("Esperando a que se completen todas las subidas...")  
    start_time = time.time()  

    while True:  
        pending_uploads = driver.find_elements(By.CSS_SELECTOR, ".dz-preview:not(.dz-success)")  
        if not pending_uploads:  
            print("Todas las subidas se han completado.")  
            return True  

        for pending in pending_uploads:  
            file_name = pending.find_element(By.CSS_SELECTOR, ".dz-filename span").text  
            progress = pending.find_element(By.CSS_SELECTOR, ".dz-progress span").get_attribute("style")  
            print(f"Archivo pendiente: {file_name}, progreso: {progress}")  

        if time.time() - start_time > max_wait:  
            print("Archivos que no se subieron:")  
            for pending in pending_uploads:  
                file_name = pending.find_element(By.CSS_SELECTOR, ".dz-filename span").text  
                print(f"  - {file_name}")  
            raise TimeoutError("Se agotó el tiempo de espera. Algunos archivos no se subieron correctamente.")  

        time.sleep(5)  

def replicate_structure(driver, local_path):  
    # Navegar primero al directorio FOLIO  
    folder_root = WebDriverWait(driver, 10).until(  
        EC.presence_of_element_located((By.LINK_TEXT, COORDINACION_FOLDER))  
    )  
    folder_root.click()  

    folio_folder = WebDriverWait(driver, 10).until(  
        EC.presence_of_element_located((By.LINK_TEXT, FOLIO))  
    )  
    folio_folder.click()  

    if CURRENT_HDD:  
        try:  
            current_hdd_folder = WebDriverWait(driver, 10).until(  
                EC.presence_of_element_located((By.LINK_TEXT, CURRENT_HDD))  
            )  
            current_hdd_folder.click()  
        except Exception as e:  
            print(f"Error al navegar a la carpeta '{CURRENT_HDD}': {e}")  
            print("Continuando sin usar CURRENT_HDD...")  
    else:  
        print("CURRENT_HDD no tiene un valor definido. Ignorando esta carpeta...")  

    for root, dirs, files in os.walk(local_path):  
        # Filtrar carpetas ocultas  
        dirs[:] = [d for d in dirs if not is_hidden(os.path.join(root, d))]  
        relative_path = os.path.relpath(root, local_path).replace("\\", "/")  
        if relative_path == ".":  
            # Para archivos en la raíz, subirlos directamente al FOLIO  
            for file in files:  
                file_path = os.path.join(root, file)  
                upload_file(driver, file_path)  
            continue  

        # Crear y navegar la estructura de carpetas  
        path_parts = relative_path.split("/")  
        current_level = 0  

        for part in path_parts:  
            try:  
                create_remote_folder(driver, part)  
                folder_link = WebDriverWait(driver, 10).until(  
                    EC.presence_of_element_located((By.LINK_TEXT, part))  
                )  
                folder_url = folder_link.get_attribute("href")  
                folder_url_with_suffix = ensure_folder_suffix(folder_url)  
                driver.get(folder_url_with_suffix)  
                current_level += 1  
            except Exception as e:  
                print(f"Error al navegar a la carpeta '{part}': {e}")  
                sys.exit(1)  

        # Subir archivos en la carpeta actual  
        for file in files:  
            file_path = os.path.join(root, file)  
            upload_file(driver, file_path)  

        # Regresar al directorio del FOLIO  
        for _ in range(current_level):  
            driver.back()  

# Configuración del WebDriver  
service = Service(DRIVER_ROOT)  
driver = webdriver.Chrome(service=service)  

try:  
    # Inicio de sesión  
    driver.get("https://repositoriot.inah.gob.mx/arrastrar/index.php")  
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "correo")))  
    driver.find_element(By.NAME, "correo").send_keys(CORREO)  
    driver.find_element(By.NAME, "contrasenia").send_keys(CONTRASENIA)  
    driver.find_element(By.NAME, "iniciar").click()  

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "file_upload")))  
    print("Inicio de sesión exitoso")  

    # Replicar estructura local siempre dentro del FOLIO  
    replicate_structure(driver, LOCAL_ROOT)  

    print("Estructura replicada exitosamente")  

finally:  
    driver.quit()  