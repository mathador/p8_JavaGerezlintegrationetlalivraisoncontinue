import subprocess
import os
import sys
import json
import shutil
import platform

# ---- Constantes (messages et commandes réutilisées) -----------------
# Messages généraux
MSG_CHECK_DEP = "🔍 Vérification des dépendances..."
MSG_NODE_NOT_INSTALLED = "❌ Node.js n'est pas installé!"
MSG_NPM_NOT_INSTALLED = "❌ npm n'est pas installé!"
MSG_DEP_INSTALLED = "✅ Dépendances installées avec succès!"
MSG_DEP_FOUND = "✅ Dépendances trouvées!"

MSG_CHECK_JAVA = "🔍 Vérification des dépendances Java/Gradle..."
MSG_JAVA_NOT_FOUND = "❌ Java n'est pas installé ou n'est pas dans le PATH!"
MSG_JAVAC_NOT_FOUND = "⚠️ `javac` non trouvé — assurez-vous d'avoir un JDK (pas seulement un JRE)."
MSG_WRAPPER_DETECTED = "ℹ️ Wrapper Gradle détecté: {wrapper} — vérification rapide..."
MSG_WRAPPER_FAIL = "❌ Échec lors de l'exécution de {wrapper} --version"
MSG_GRADLE_NOT_FOUND = "❌ Gradle non trouvé. Installez Gradle ou ajoutez le wrapper 'gradlew' au projet."

MSG_CLEANING = "🧹 Nettoyage des artefacts de tests précédents..."
MSG_TESTS_RUNNING = "🚀 Lancement des tests..."
MSG_TESTS_OK = "✅ Tests réussis!"
MSG_TESTS_KO = "❌ Tests échoués!"

# Commandes réutilisées
CMD_NODE_VERSION = ["node", "--version"]
CMD_NPM_VERSION = ["npm", "--version"]
CMD_NPM_INSTALL = ["npm", "install"]
CMD_JAVA_VERSION = ["java", "-version"]
CMD_JAVAC_VERSION = ["javac", "-version"]
CMD_GRADLE_VERSION = ["gradle", "--version"]

DEFAULT_PYTHON = "3.11"

# ---------------------------------------------------------------------


def check_dependencies_for_npm():
    """Vérifier l'existence des dépendances Node.js et npm."""
    print(MSG_CHECK_DEP)

    # Vérifier que Node.js est installé
    node_check = run_process(CMD_NODE_VERSION)
    if node_check.returncode != 0:
        print(MSG_NODE_NOT_INSTALLED)
        return False
    print(f"✅ Node.js détecté: {first_output_line(node_check)}")

    # Vérifier que npm est installé
    npm_check = run_process(CMD_NPM_VERSION)
    if npm_check.returncode != 0:
        print(MSG_NPM_NOT_INSTALLED)
        return False
    print(f"✅ npm détecté: {first_output_line(npm_check)}")

    # Vérifier que node_modules existe, sinon l'installer
    if not os.path.exists("node_modules"):
        print("⚠️ node_modules non trouvé. Installation des dépendances...")
        install = run_process(CMD_NPM_INSTALL, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if install.returncode != 0:
            print("❌ Erreur lors de l'installation des dépendances!")
            print(install.stderr)
            return False
        print(MSG_DEP_INSTALLED)
    else:
        print("✅ Dépendances trouvées!")

    return True


def check_dependencies_for_gradle():
    """Vérifier l'existence des dépendances Java et Gradle."""
    print(MSG_CHECK_JAVA)

    # Vérifier que Java est installé
    java_check = run_process(CMD_JAVA_VERSION)
    if java_check.returncode != 0:
        print(MSG_JAVA_NOT_FOUND)
        if java_check.stderr:
            print(java_check.stderr)
        return False
    # java -version écrit souvent sur stderr
    java_version = (java_check.stdout or java_check.stderr or "").strip().splitlines()[0]
    print(f"✅ Java détecté: {java_version}")

    # Vérifier que javac est installé (JDK)
    javac_check = run_process(CMD_JAVAC_VERSION)
    if javac_check.returncode != 0:
        print("⚠️ `javac` non trouvé — assurez-vous d'avoir un JDK (pas seulement un JRE).")
    else:
        javac_version = (javac_check.stdout or javac_check.stderr or "").strip().splitlines()[0]
        print(f"✅ Javac détecté: {javac_version}")

    # Préférer le wrapper Gradle si présent
    gradlew = "gradlew"
    gradlewbat = f"{gradlew}.bat"
    if os.path.exists(gradlew) or os.path.exists("./" + gradlew):
        wrapper = gradlew if os.path.exists(gradlew) else gradlewbat
        print(MSG_WRAPPER_DETECTED.format(wrapper=wrapper))
        try:
            wrapper_check = run_process([wrapper, "--version"]) if os.path.exists(wrapper) else run_process(["./" + wrapper, "--version"]) 
            if wrapper_check.returncode != 0:
                print(MSG_WRAPPER_FAIL.format(wrapper=wrapper))
                if wrapper_check.stderr:
                    print(wrapper_check.stderr)
                return False
            print("✅ Wrapper Gradle fonctionnel.")
            return True
        except Exception as e:
            print(MSG_WRAPPER_FAIL.format(wrapper=wrapper))
            print(f"Exception: {e}")
            wrapper = gradlew
            try:
                wrapper_check = run_process([wrapper, "--version"]) if os.path.exists(wrapper) else run_process(["./" + wrapper, "--version"]) 
                if wrapper_check.returncode != 0:
                    print(MSG_WRAPPER_FAIL.format(wrapper=wrapper))
                    if wrapper_check.stderr:
                        print(wrapper_check.stderr)
                    return False
                print("✅ Wrapper Gradle fonctionnel.")
                return True
            except Exception as e:
                return False

    # Sinon vérifier installation globale de gradle
    gradle_check = run_process(CMD_GRADLE_VERSION)
    if gradle_check.returncode != 0:
        print(MSG_GRADLE_NOT_FOUND)
        if gradle_check.stderr:
            print(gradle_check.stderr)
        return False

    gradle_version = (gradle_check.stdout or gradle_check.stderr or "").strip().splitlines()[0]
    print(f"✅ Gradle détecté: {gradle_version}")
    return True


def clean_test_artifacts(junitxml_output_dir="test-results"):
    """Nettoyer les artefacts de tests précédents."""
    print("\n🧹 Nettoyage des artefacts de tests précédents...")

    # Supprimer le dossier junitxml_output_dir s'il existe
    if os.path.exists(junitxml_output_dir):
        shutil.rmtree(junitxml_output_dir)
        print(f"✅ Dossier {junitxml_output_dir} supprimé!")

    # Supprimer les fichiers de cache de karma s'ils existent
    if os.path.exists(".karma"):
        shutil.rmtree(".karma")
        print("✅ Cache Karma supprimé!")


def run_tests(command):
    """Lancer les tests (Angular ou Java selon la commande)."""
    print("\n" + MSG_TESTS_RUNNING)
    output = run_process(command, capture_output=True,
                         text=True, encoding='utf-8', errors='replace')

    return output.returncode


def run_process(cmd, capture_output=True, text=True, encoding=None, errors=None):
    """Exécute une commande de façon compatible Windows / POSIX.

    - Sur Windows, utilise `shell=True` pour supporter les commandes formatées.
    - Sur POSIX, exécute la commande directement (liste recommandée).
    """
    is_windows = platform.system().lower().startswith("win")
    # Si la commande est une liste, la préparer pour shell sur Windows
    if is_windows:
        # Joindre en string pour shell=True
        if isinstance(cmd, (list, tuple)):
            cmd_str = " ".join(cmd)
        else:
            cmd_str = cmd
        return subprocess.run(cmd_str, capture_output=capture_output, text=text, encoding=encoding, errors=errors, shell=True)
    else:
        # POSIX: si on reçoit une string, exécuter via shell=False peut échouer,
        # donc passer la string au shell si nécessaire.
        if isinstance(cmd, (list, tuple)):
            return subprocess.run(list(cmd), capture_output=capture_output, text=text, encoding=encoding, errors=errors)
        else:
            return subprocess.run(cmd, capture_output=capture_output, text=text, encoding=encoding, errors=errors, shell=True)


def first_output_line(proc_result):
    """Retourne la première ligne non vide de stdout ou stderr d'un résultat subprocess."""
    out = (proc_result.stdout or proc_result.stderr or "").strip()
    return out.splitlines()[0] if out else ""


def get_gradle_command():
    """Retourne la commande Gradle adaptée à la plateforme et au projet.

    Priorité: `gradlew.bat` > `gradlew` (./gradlew sur POSIX) > `gradle`.
    """
    if os.path.exists("gradlew.bat"):
        return "gradlew.bat"
    if os.path.exists("gradlew"):
        # utiliser le wrapper local explicitement sous POSIX
        return "./gradlew" if not platform.system().lower().startswith("win") else "gradlew"
    return "gradle"


def detect_project_type():
    # Angular si angular.json présent ou package.json contenant des scripts Angular
    if os.path.exists("angular.json"):
        return "angular"
    if os.path.exists("package.json"):
        try:
            with open("package.json", "r", encoding="utf-8") as f:
                pj = json.load(f)
                scripts = pj.get("scripts", {}) or {}
                # script test qui appelle "ng" ou présence de dépendances Angular
                test_script = scripts.get("test", "")
                if "ng" in test_script or any(k.startswith("@angular/") for k in pj.get("dependencies", {})):
                    return "angular"
        except Exception:
            pass

    # Java si build.gradle ou gradlew existe ou pom.xml
    if os.path.exists("build.gradle") or os.path.exists("gradlew") or os.path.exists("gradlew.bat") or os.path.exists("pom.xml"):
        return "java"

    return "unknown"


def main():
    """Fonction principale."""
    # valeur par défaut en cas d'erreur avant exécution des tests
    returncode = 1
    try:
        # Commandes multi-plateforme (éviter 'cmd /c')
        angular_command = ["npm", "test"]
        if os.path.exists("gradlew.bat"):
            gradlew_cmd = "gradlew.bat"
        elif os.path.exists("gradlew"):
            # appeler le wrapper local explicitement sous POSIX
            gradlew_cmd = "./gradlew"
        else:
            gradlew_cmd = "gradle"
        java_command = [gradlew_cmd, "clean", "test"]
        output_test_dir = "build/test-results"

        # Détecter si le projet est Angular ou Java et ajuster les commandes en conséquence
        project_type = detect_project_type()

        # Ajuster en conséquence
        if project_type == "angular":
            print("ℹ️ Projet détecté: Angular. Utilisation de `npm test`.")

            # Vérifier les dépendances Node seulement pour Angular
            if not check_dependencies_for_npm():
                print("\n❌ Vérification des dépendances échouée!")
                sys.exit(1)

            output_test_dir = "test-results"
            command = angular_command

        elif project_type == "java":
            print("ℹ️ Projet détecté: Java. Utilisation de Gradle pour lancer les tests.")

            # Vérifier les dépendances Gradle seulement pour Java
            if not check_dependencies_for_gradle():
                print("\n❌ Vérification des dépendances échouée!")
                sys.exit(1)

            output_test_dir = "build/test-results"
            command = java_command

        else:
            print(
                "⚠️ Type de projet non détecté. Utilisation par défaut de la commande Gradle si disponible.")
            sys.exit(1)

        # Étape 2: Nettoyer les artefacts
        clean_test_artifacts(output_test_dir)

        # Étape 3: Lancer les tests
        returncode = run_tests(command)

        # Étape 4: Afficher le résultat final
        if returncode == 0:
            print("\n✅ Tests réussis!")
        else:
            print("\n❌ Tests échoués!")

    except Exception as e:
        print(f"\n❌ Erreur: {e}")

    sys.exit(returncode)


if __name__ == "__main__":
    main()
