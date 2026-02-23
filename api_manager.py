#!/usr/bin/env python3
"""
Secure API Key Manager
Gestión segura de API keys con encriptación Fernet
"""

import os
import json
from pathlib import Path
from cryptography.fernet import Fernet
from typing import Dict, Optional


class APIKeyManager:
    """Gestiona API keys de forma segura con encriptación"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Inicializa el gestor de API keys
        
        Args:
            config_dir: Directorio para almacenar configuración (por defecto: ./config)
        """
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent / 'config'
        self.config_dir.mkdir(exist_ok=True)
        
        self.key_file = self.config_dir / '.api_encryption_key'
        self.config_file = self.config_dir / 'api_keys.enc'
        
        self.cipher = self._get_or_create_cipher()
    
    def _get_or_create_cipher(self) -> Fernet:
        """Obtiene o crea una clave de encriptación"""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Proteger el archivo de claves (solo lectura/escritura para el propietario)
            os.chmod(self.key_file, 0o600)
        
        return Fernet(key)
    
    def save_api_keys(self, api_keys: Dict[str, str]) -> bool:
        """
        Guarda las API keys de forma segura (encriptadas)
        
        Args:
            api_keys: Diccionario con las API keys {source: key}
        
        Returns:
            True si se guardó correctamente, False en caso de error
        """
        try:
            # Filtrar keys vacías
            filtered_keys = {k: v for k, v in api_keys.items() if v and v.strip()}
            
            # Serializar a JSON
            json_data = json.dumps(filtered_keys)
            
            # Encriptar
            encrypted_data = self.cipher.encrypt(json_data.encode('utf-8'))
            
            # Guardar en archivo
            with open(self.config_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Proteger el archivo (solo lectura/escritura para el propietario)
            os.chmod(self.config_file, 0o600)
            
            return True
        except Exception as e:
            print(f"Error saving API keys: {e}")
            return False
    
    def load_api_keys(self) -> Dict[str, str]:
        """
        Carga las API keys desde el almacenamiento seguro
        
        Returns:
            Diccionario con las API keys {source: key}
        """
        if not self.config_file.exists():
            return {}
        
        try:
            # Leer archivo encriptado
            with open(self.config_file, 'rb') as f:
                encrypted_data = f.read()
            
            # Desencriptar
            decrypted_data = self.cipher.decrypt(encrypted_data)
            
            # Deserializar JSON
            api_keys = json.loads(decrypted_data.decode('utf-8'))
            
            return api_keys
        except Exception as e:
            print(f"Error loading API keys: {e}")
            return {}
    
    def get_api_key(self, source: str) -> Optional[str]:
        """
        Obtiene una API key específica
        
        Args:
            source: Nombre de la fuente (virustotal, abuseipdb, etc.)
        
        Returns:
            API key si existe, None si no
        """
        api_keys = self.load_api_keys()
        return api_keys.get(source)
    
    def set_api_key(self, source: str, api_key: str) -> bool:
        """
        Establece o actualiza una API key específica
        
        Args:
            source: Nombre de la fuente
            api_key: API key a guardar
        
        Returns:
            True si se guardó correctamente
        """
        api_keys = self.load_api_keys()
        api_keys[source] = api_key
        return self.save_api_keys(api_keys)
    
    def delete_api_key(self, source: str) -> bool:
        """
        Elimina una API key específica
        
        Args:
            source: Nombre de la fuente
        
        Returns:
            True si se eliminó correctamente
        """
        api_keys = self.load_api_keys()
        if source in api_keys:
            del api_keys[source]
            return self.save_api_keys(api_keys)
        return False
    
    def get_api_status(self) -> Dict[str, bool]:
        """
        Obtiene el estado de configuración de las APIs
        
        Returns:
            Diccionario {source: True/False} indicando si está configurada
        """
        api_keys = self.load_api_keys()
        
        all_sources = [
            'virustotal', 'abuseipdb', 'alienvault_otx', 'urlscan', 
            'hybrid_analysis', 'malware_bazaar', 'shodan', 'urlvoid',
            'securitytrails', 'whois_info', 'criminalip', 'cisco_talos',
            'mxtoolbox', 'ip_geolocation', 'viewdns', 'centralops',
            'dnslytics', 'ipthc', 'synapsint', 'ipapi', 'ipdata', 'apivoid'
        ]
        
        return {source: bool(api_keys.get(source)) for source in all_sources}
    
    def clear_all_keys(self) -> bool:
        """
        Elimina todas las API keys
        
        Returns:
            True si se eliminaron correctamente
        """
        return self.save_api_keys({})
    
    def export_keys_to_env(self) -> str:
        """
        Exporta las API keys en formato de variables de entorno
        
        Returns:
            String con las variables de entorno
        """
        api_keys = self.load_api_keys()
        env_vars = []
        
        env_mapping = {
            'virustotal': 'VIRUSTOTAL_API_KEY',
            'abuseipdb': 'ABUSEIPDB_API_KEY',
            'securitytrails': 'ST_API_KEY',
            'shodan': 'SHODAN_API_KEY',
            'urlscan': 'URLSCAN_API_KEY',
            'ipapi': 'IPAPI_ACCESS_KEY',
            'ipdata': 'IPDATA_API_KEY',
            'apivoid': 'APIVOID_KEY',
            'abusech': 'ABUSECH_API_KEY',
            'pdcp': 'PDCP_API_KEY'
        }
        
        for source, api_key in api_keys.items():
            env_var = env_mapping.get(source, f"{source.upper()}_API_KEY")
            env_vars.append(f"export {env_var}=\"{api_key}\"")
        
        return "\n".join(env_vars)
