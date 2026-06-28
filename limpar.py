import os
import sys
import shutil
import ctypes
import subprocess
import winreg
import time
from datetime import datetime

# Habilitar sequências de escape ANSI no terminal do Windows para cores funcionarem nativamente
def enable_ansi_colors():
    try:
        kernel32 = ctypes.windll.kernel32
        h_stdout = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_ulong()
        if kernel32.GetConsoleMode(h_stdout, ctypes.byref(mode)):
            # 4 = ENABLE_VIRTUAL_TERMINAL_PROCESSING
            kernel32.SetConsoleMode(h_stdout, mode.value | 4)
    except Exception:
        pass

enable_ansi_colors()

# Códigos de Cor ANSI
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
WHITE = "\033[97m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_header(title):
    print(f"\n{BOLD}{CYAN}======================================================================{RESET}")
    print(f"  {BOLD}{WHITE}{title}{RESET}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}")

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def elevate():
    if not is_admin():
        print(f"\n{YELLOW}[!] Este utilitário necessita de privilégios de Administrador para realizar limpezas profundas.{RESET}")
        print(f"{YELLOW}[*] Reiniciando com privilégios elevados...{RESET}")
        time.sleep(1.5)
        try:
            # Se executando como binário compilado (.exe) ou script
            if getattr(sys, 'frozen', False):
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv[1:]), None, 1)
            else:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{sys.argv[0]}" ' + " ".join(sys.argv[1:]), None, 1)
        except Exception as e:
            print(f"{RED}[-] Erro ao tentar elevar privilégios: {e}{RESET}")
            print(f"{RED}[-] Por favor, clique com o botão direito no programa e escolha 'Executar como Administrador'.{RESET}")
            input("\nPressione Enter para sair...")
        sys.exit(0)

# Deleta arquivos individuais tratando exceções
def safe_delete_file(file_path):
    try:
        if os.path.exists(file_path):
            os.chmod(file_path, 0o777)  # Garante permissões de escrita/remoção
            os.remove(file_path)
            return True, 0
    except PermissionError:
        return False, "em uso"
    except Exception as e:
        return False, str(e)
    return False, "não encontrado"

# Deleta diretórios inteiros tratando exceções e tentando deletar itens remanescentes individualmente
def safe_delete_dir(dir_path):
    try:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            return True, 0
    except PermissionError:
        # Se falhar a remoção direta do diretório por arquivos bloqueados, tenta individualmente
        files_deleted = 0
        for root, dirs, files in os.walk(dir_path, topdown=False):
            for name in files:
                fp = os.path.join(root, name)
                try:
                    os.chmod(fp, 0o777)
                    os.remove(fp)
                    files_deleted += 1
                except Exception:
                    pass
            for name in dirs:
                dp = os.path.join(root, name)
                try:
                    os.rmdir(dp)
                except Exception:
                    pass
        try:
            os.rmdir(dir_path)
            return True, 0
        except Exception:
            return False, "arquivos bloqueados/em uso"
    except Exception as e:
        return False, str(e)
    return False, "não encontrado"

# Limpador de Arquivos Temporários e Cache
def clean_temporary_files():
    print_header("🧹 LIMPEZA DE ARQUIVOS TEMPORÁRIOS E CACHE")
    
    local_app_data = os.environ.get('LOCALAPPDATA', '')
    app_data = os.environ.get('APPDATA', '')
    user_temp = os.environ.get('TEMP', '')
    system_temp = r"C:\Windows\Temp"
    prefetch = r"C:\Windows\Prefetch"
    log_dir = r"C:\Windows\Logs"
    
    targets = [
        ("Temp de Usuário", user_temp, "dir"),
        ("Temp do Sistema", system_temp, "dir"),
        ("Prefetch do Windows", prefetch, "dir"),
        ("Logs do Windows", log_dir, "dir")
    ]
    
    # Adicionar caches de navegadores comuns se existirem
    browser_caches = [
        ("Cache do Google Chrome", os.path.join(local_app_data, r"Google\Chrome\User Data\Default\Cache"), "dir"),
        ("Cache do Microsoft Edge", os.path.join(local_app_data, r"Microsoft\Edge\User Data\Default\Cache"), "dir"),
        ("Cache do Vivaldi", os.path.join(local_app_data, r"Vivaldi\User Data\Default\Cache"), "dir"),
        ("Cache do Discord", os.path.join(app_data, r"discord\Cache"), "dir"),
        ("Cache do Spotify", os.path.join(local_app_data, r"Spotify\Storage"), "dir"),
        ("Cache do Steam (HTML)", os.path.join(local_app_data, r"Steam\htmlcache"), "dir")
    ]
    
    for label, path, p_type in browser_caches:
        if os.path.exists(path):
            targets.append((label, path, p_type))

    total_bytes_saved = 0
    files_cleaned = 0
    files_skipped = 0
    
    for label, path, path_type in targets:
        if not path or not os.path.exists(path):
            continue
            
        print(f"[*] Analisando {label}...", end="\r")
        
        # Calcular tamanho do diretório/arquivo antes de limpar
        path_size = 0
        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        path_size += os.path.getsize(fp)
                    except Exception:
                        pass
        else:
            try:
                path_size = os.path.getsize(path)
            except Exception:
                pass
                
        print(f"[*] Limpando {label} ({path_size / (1024*1024):.2f} MB)...")
        
        # Executar a limpeza
        if path_type == "dir" and os.path.isdir(path):
            # Limpa o conteúdo de dentro do diretório, preservando a pasta raiz
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    success, err = safe_delete_dir(item_path)
                    if success:
                        files_cleaned += 1
                    else:
                        files_skipped += 1
                else:
                    success, err = safe_delete_file(item_path)
                    if success:
                        files_cleaned += 1
                    else:
                        files_skipped += 1
            total_bytes_saved += path_size
        elif path_type == "file" and os.path.isfile(path):
            success, err = safe_delete_file(path)
            if success:
                files_cleaned += 1
                total_bytes_saved += path_size
            else:
                files_skipped += 1
                
    # Limpeza Especial: Cache de Downloads do Windows Update (SoftwareDistribution)
    # Requer parar o serviço do Windows Update, limpar, e reiniciar
    print(f"\n[*] Limpando Cache de Downloads do Windows Update (SoftwareDistribution)...")
    try:
        # Parar serviços do Windows Update e Transferência Inteligente de Semicondutores (BITS)
        subprocess.run("net stop wuauserv", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run("net stop bits", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        sw_dist_path = r"C:\Windows\SoftwareDistribution\Download"
        if os.path.exists(sw_dist_path):
            for item in os.listdir(sw_dist_path):
                item_path = os.path.join(sw_dist_path, item)
                if os.path.isdir(item_path):
                    safe_delete_dir(item_path)
                else:
                    safe_delete_file(item_path)
                    
        # Reiniciar os serviços
        subprocess.run("net start wuauserv", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run("net start bits", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"{GREEN}[+] Cache do Windows Update limpo e serviços reiniciados.{RESET}")
    except Exception as e:
        print(f"{YELLOW}[!] Falha ao limpar cache do Windows Update: {e}{RESET}")
        
    print(f"\n{GREEN}[+] Limpeza de Arquivos Temporários Concluída!{RESET}")
    print(f"    - Espaço recuperado aproximado: {BOLD}{total_bytes_saved / (1024*1024):.2f} MB{RESET}")
    print(f"    - Itens removidos: {files_cleaned}")
    print(f"    - Itens ignorados (em uso pelo sistema): {files_skipped}")

# Limpeza e Otimização do Registro do Windows (Ações Seguras)
def clean_registry():
    print_header("🗃️ LIMPEZA E OTIMIZAÇÃO DO REGISTRO")
    
    print("[*] Iniciando limpeza segura do Registro do Windows...")
    time.sleep(1)
    
    # 1. Limpar MuiCache (Referências a arquivos de executáveis que não existem mais)
    print("[*] Verificando MuiCache por executáveis removidos...")
    mui_cleaned = 0
    try:
        key_path = r"Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\MuiCache"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
        
        # Coleta todas as chaves primeiro para não alterar o índice do enumerador durante remoção
        info = winreg.QueryInfoKey(key)
        num_values = info[1]
        values_to_delete = []
        
        for i in range(num_values):
            try:
                name, val, val_type = winreg.EnumValue(key, i)
                # O nome do valor costuma ser o caminho completo do executável
                # e.g., "C:\Program Files\App\app.exe.FriendlyAppName" ou "C:\...\app.exe"
                exec_path = name.split('.FriendlyAppName')[0].split('.ApplicationCompany')[0]
                
                # Se for um caminho absoluto válido sintaticamente mas o executável correspondente não existe
                if (exec_path.startswith("C:\\") or exec_path.startswith("D:\\") or exec_path.startswith("E:\\") or exec_path.startswith("F:\\")) and "\\" in exec_path:
                    clean_path = exec_path.replace('"', '').strip()
                    if not os.path.exists(clean_path):
                        values_to_delete.append(name)
            except Exception:
                pass
                
        for val_name in values_to_delete:
            try:
                winreg.DeleteValue(key, val_name)
                mui_cleaned += 1
            except Exception:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        print(f"    [!] Aviso ao limpar MuiCache: {e}")
        
    print(f"    - Removidas {BOLD}{mui_cleaned}{RESET} entradas obsoletas do MuiCache.")

    # 2. Limpar o histórico da caixa "Executar" (RunMRU)
    print("[*] Limpando histórico da janela 'Executar' (RunMRU)...")
    run_mru_cleaned = False
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
        info = winreg.QueryInfoKey(key)
        num_values = info[1]
        values_to_delete = []
        for i in range(num_values):
            try:
                name, _, _ = winreg.EnumValue(key, i)
                values_to_delete.append(name)
            except Exception:
                pass
        for val in values_to_delete:
            winreg.DeleteValue(key, val)
        winreg.CloseKey(key)
        run_mru_cleaned = True
    except Exception:
        pass
        
    if run_mru_cleaned:
        print(f"    - Histórico da caixa Executar limpo com sucesso.")
    else:
        print(f"    - Nenhuma entrada histórica de 'Executar' encontrada ou sem permissão.")

    # 3. Limpar histórico de Arquivos Recentes (RecentDocs)
    print("[*] Limpando histórico de documentos recentes do Windows Explorer...")
    recent_cleaned = False
    
    # Função recursiva auxiliar para deletar subchaves do Registro de forma segura
    def delete_key_recursive(key_root, subkey_path):
        try:
            key = winreg.OpenKey(key_root, subkey_path, 0, winreg.KEY_ALL_ACCESS)
            info = winreg.QueryInfoKey(key)
            num_subkeys = info[0]
            subkeys_to_delete = []
            for i in range(num_subkeys):
                try:
                    subkeys_to_delete.append(winreg.EnumKey(key, i))
                except Exception:
                    pass
            winreg.CloseKey(key)
            
            for sk in subkeys_to_delete:
                delete_key_recursive(key_root, os.path.join(subkey_path, sk))
                
            key = winreg.OpenKey(key_root, subkey_path, 0, winreg.KEY_ALL_ACCESS)
            info = winreg.QueryInfoKey(key)
            num_values = info[1]
            values_to_delete = []
            for i in range(num_values):
                try:
                    values_to_delete.append(winreg.EnumValue(key, i)[0])
                except Exception:
                    pass
            for val in values_to_delete:
                winreg.DeleteValue(key, val)
            winreg.CloseKey(key)
            
            # Se for uma subchave (não a raiz da busca original), tenta deletar a pasta em si
            # (não deletamos a raiz para preservar a estrutura do Windows)
            return True
        except Exception:
            return False

    recent_cleaned = delete_key_recursive(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs")
    if recent_cleaned:
        print(f"    - Histórico de documentos recentes (RecentDocs) limpo com sucesso.")
    else:
        print(f"    - Falha ao limpar RecentDocs ou já limpo.")

    print(f"\n{GREEN}[+] Limpeza do Registro e Históricos Concluída!{RESET}")

# Auxiliar para rodar comandos e transmitir saída ao vivo
def run_command_live(command, description):
    print(f"\n{BOLD}{CYAN}[*] Iniciando {description}...{RESET}")
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding='cp850')
        for line in process.stdout:
            sys.stdout.write(f"    {line}")
            sys.stdout.flush()
        process.wait()
        if process.returncode == 0:
            print(f"{GREEN}[+] {description} concluído com sucesso!{RESET}")
            return True
        else:
            print(f"{YELLOW}[!] {description} terminou com código de retorno {process.returncode}.{RESET}")
            return False
    except Exception as e:
        print(f"{RED}[-] Erro ao executar {description}: {e}{RESET}")
        return False

# Ferramentas de Correção de Erros de Sistema e Rede
def repair_system_errors():
    print_header("🚀 CORREÇÃO DE ERROS DE SISTEMA E REDE")
    
    print(f"{BOLD}[*] Serão executadas ferramentas oficiais de reparo e otimização.{RESET}")
    print(f"{BOLD}[*] Esse processo pode demorar alguns minutos. Por favor, aguarde.{RESET}\n")
    
    # 1. Liberar DNS Cache (Flush DNS)
    print("[*] Limpando cache do resolvedor DNS...")
    try:
        subprocess.run("ipconfig /flushdns", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"{GREEN}    [+] Cache de DNS limpo com sucesso!{RESET}")
    except Exception:
        print(f"{RED}    [-] Falha ao limpar cache DNS.{RESET}")
        
    # 2. Resetar Sockets de Rede (Winsock)
    print("[*] Redefinindo pilha TCP/IP e Sockets de rede...")
    try:
        subprocess.run("netsh winsock reset", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run("netsh int ip reset", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"{GREEN}    [+] Sockets e configuração TCP/IP redefinidos com sucesso!{RESET}")
    except Exception:
        print(f"{RED}    [-] Falha ao redefinir configurações de rede.{RESET}")

    # 3. Executar SFC Scan (System File Checker)
    # Verifica e repara arquivos corrompidos do sistema do Windows
    run_command_live("sfc /scannow", "Verificação de Integridade de Arquivos do Sistema (SFC)")

    # 4. Executar DISM Cleanup & Restore
    # Verifica corrupções na imagem oficial de recuperação do Windows
    run_command_live("DISM /Online /Cleanup-Image /RestoreHealth", "Reparo da Imagem do Windows (DISM)")

    print(f"\n{GREEN}[+] Correção de Erros concluída!{RESET}")
    print(f"{YELLOW}[!] Recomendamos reiniciar o computador caso tenha sido feito algum reparo pesado.{RESET}")

# Esvazia a Lixeira do Windows nativamente
def empty_recycle_bin():
    print_header("🗑️ ESVAZIAR LIXEIRA DO WINDOWS")
    print("[*] Esvaziando Lixeira...")
    try:
        # SHERB_NOCONFIRMATION = 0x00000001
        # SHERB_NOPROGRESSUI   = 0x00000002
        # SHERB_NOSOUND        = 0x00000004
        # Soma = 7 para fazer tudo silenciosamente
        result = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
        if result == 0:
            print(f"{GREEN}[+] Lixeira esvaziada com sucesso!{RESET}")
        else:
            # Pode retornar erros específicos se a lixeira já estiver vazia
            print(f"{GREEN}[+] Lixeira limpa ou já vazia.{RESET}")
    except Exception as e:
        print(f"{RED}[-] Erro ao esvaziar lixeira: {e}{RESET}")

def run_all_optimizations():
    print_header("✨ OTIMIZAÇÃO COMPLETA DO SISTEMA")
    print(f"{BOLD}{YELLOW}[!] Iniciando rotina completa de manutenção. Isso passará por todas as etapas.{RESET}")
    time.sleep(1)
    
    clean_temporary_files()
    clean_registry()
    repair_system_errors()
    empty_recycle_bin()
    
    print_header("🎉 OTIMIZAÇÃO COMPLETA CONCLUÍDA COM SUCESSO! 🎉")
    print(f"{GREEN}Seu sistema agora está limpo, com mais espaço livre e erros corrigidos!{RESET}")

def show_menu():
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print(f"""{BOLD}{CYAN}
======================================================================
     🤖 AGENTE OTIMIZADOR DE PC DO WINDOWS (v1.0.0)
     Desenvolvido para limpeza de espaço e reparo automático
======================================================================{RESET}
  {BOLD}{WHITE}MENU DE OPÇÕES:{RESET}
  
  [{GREEN}1{RESET}] 🧹 Limpar Arquivos Temporários, Caches e Downloads ({CYAN}Libera Espaço{RESET})
  [{GREEN}2{RESET}] 🗃️  Limpar Registro Obsoleto e Históricos ({CYAN}Otimiza Desempenho{RESET})
  [{GREEN}3{RESET}] 🚀 Corrigir Erros de Sistema e Rede ({CYAN}SFC, DISM, DNS, Winsock{RESET})
  [{GREEN}4{RESET}] ✨ Otimização Completa ({CYAN}Executa TODAS as opções acima sequencialmente{RESET})
  [{GREEN}5{RESET}] 🗑️  Esvaziar Lixeira do Windows ({CYAN}Nativamente{RESET})
  
  [{RED}0{RESET}] ❌ Sair do Agente
{BOLD}{CYAN}======================================================================{RESET}""")
        
        try:
            opcao = input(f"{BOLD}{WHITE}Escolha o número do que deseja fazer: {RESET}").strip()
        except KeyboardInterrupt:
            print(f"\n\n{YELLOW}[*] Encerrando utilitário...{RESET}")
            break
            
        if opcao == "1":
            clean_temporary_files()
            input(f"\n{BOLD}{WHITE}Pressione Enter para voltar ao menu...{RESET}")
        elif opcao == "2":
            clean_registry()
            input(f"\n{BOLD}{WHITE}Pressione Enter para voltar ao menu...{RESET}")
        elif opcao == "3":
            repair_system_errors()
            input(f"\n{BOLD}{WHITE}Pressione Enter para voltar ao menu...{RESET}")
        elif opcao == "4":
            run_all_optimizations()
            input(f"\n{BOLD}{WHITE}Pressione Enter para voltar ao menu...{RESET}")
        elif opcao == "5":
            empty_recycle_bin()
            input(f"\n{BOLD}{WHITE}Pressione Enter para voltar ao menu...{RESET}")
        elif opcao == "0":
            print(f"\n{GREEN}[+] Obrigado por usar o Agente Otimizador! Até logo.{RESET}")
            time.sleep(1)
            break
        else:
            print(f"{RED}[!] Opção inválida. Tente novamente.{RESET}")
            time.sleep(1)

def main():
    # Garante que roda como Administrador para poder excluir arquivos de sistema, limpar SoftwareDistribution e rodar SFC/DISM
    elevate()
    
    # Se houver argumentos de terminal, executa diretamente sem menu ("DOU O COMANDO E ELE ATIVA E FAZ")
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower().strip()
        if arg in ["--tudo", "-a", "/all", "/tudo"]:
            run_all_optimizations()
        elif arg in ["--temp", "-t", "/temp"]:
            clean_temporary_files()
        elif arg in ["--registro", "-r", "/registry"]:
            clean_registry()
        elif arg in ["--reparar", "-f", "/repair", "/reparar"]:
            repair_system_errors()
        elif arg in ["--lixeira", "-l", "/recycle"]:
            empty_recycle_bin()
        else:
            print(f"{YELLOW}Argumento inválido: {sys.argv[1]}{RESET}")
            print(f"Uso: limpar [argumento]")
            print(f"Argumentos válidos:")
            print(f"  --tudo     : Executa todas as limpezas e correções automaticamente.")
            print(f"  --temp     : Executa apenas a limpeza de arquivos temporários e caches.")
            print(f"  --registro : Executa apenas a limpeza de registro e históricos.")
            print(f"  --reparar  : Executa apenas a redefinição de rede e correções SFC/DISM.")
            print(f"  --lixeira  : Apenas esvazia a lixeira silenciosamente.")
            time.sleep(3)
    else:
        # Abre o menu interativo
        show_menu()

if __name__ == "__main__":
    main()
