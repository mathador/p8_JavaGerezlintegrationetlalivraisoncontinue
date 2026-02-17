import subprocess
import os
import sys
import json
import shutil


def check_dependencies_for_npm():
    """Vérifier l'existence des dépendances Node.js et npm."""
    print("🔍 Vérification des dépendances...")

    # Vérifier que Node.js est installé
    node_check = subprocess.run(
        ["cmd", "/c", "node", "--version"], capture_output=True, text=True)
    if node_check.returncode != 0:
        print("❌ Node.js n'est pas installé!")
        return False
    print(f"✅ Node.js détecté: {node_check.stdout.strip()}")

    # Vérifier que npm est installé
    npm_check = subprocess.run(
        ["cmd", "/c", "npm", "--version"], capture_output=True, text=True)
    if npm_check.returncode != 0:
        print("❌ npm n'est pas installé!")
        return False
    print(f"✅ npm détecté: {npm_check.stdout.strip()}")

    # Vérifier que node_modules existe, sinon l'installer
    if not os.path.exists("node_modules"):
        print("⚠️ node_modules non trouvé. Installation des dépendances...")
        install = subprocess.run(["cmd", "/c", "npm", "install"],
                                 capture_output=True, text=True, encoding='utf-8', errors='replace')
        if install.returncode != 0:
            print("❌ Erreur lors de l'installation des dépendances!")
            print(install.stderr)
            return False
        print("✅ Dépendances installées avec succès!")
    else:
        print("✅ Dépendances trouvées!")

    return True


def check_dependencies_for_gradle():
    """Vérifier l'existence des dépendances Java et Gradle."""
    print("🔍 Vérification des dépendances Java/Gradle...")

    # Vérifier que Java est installé
    java_check = subprocess.run(
        ["cmd", "/c", "java", "-version"], capture_output=True, text=True)
    if java_check.returncode != 0:
        print("❌ Java n'est pas installé ou n'est pas dans le PATH!")
        if java_check.stderr:
            print(java_check.stderr)
        return False
    # java -version écrit souvent sur stderr
    java_version = (
        java_check.stdout or java_check.stderr or "").strip().splitlines()[0]
    print(f"✅ Java détecté: {java_version}")

    # Vérifier que javac est installé (JDK)
    javac_check = subprocess.run(
        ["cmd", "/c", "javac", "-version"], capture_output=True, text=True)
    if javac_check.returncode != 0:
        print("⚠️ `javac` non trouvé — assurez-vous d'avoir un JDK (pas seulement un JRE).")
    else:
        javac_version = (
            javac_check.stdout or javac_check.stderr or "").strip().splitlines()[0]
        print(f"✅ Javac détecté: {javac_version}")

    gradlew = "gradlew"
    gradlewbat = f"{gradlew}.bat"
    # Préférer le wrapper Gradle si présent
    if os.path.exists(gradlewbat) or os.path.exists(gradlew):
        wrapper = gradlewbat if os.path.exists(gradlewbat) else gradlew
        print(f"ℹ️ Wrapper Gradle détecté: {wrapper} — vérification rapide...")
        wrapper_check = subprocess.run(
            ["cmd", "/c", wrapper, "--version"], capture_output=True, text=True)
        if wrapper_check.returncode != 0:
            print(f"❌ Échec lors de l'exécution de {wrapper} --version")
            if wrapper_check.stderr:
                print(wrapper_check.stderr)
            return False
        print("✅ Wrapper Gradle fonctionnel.")
        return True

    # Sinon vérifier installation globale de gradle
    gradle_check = subprocess.run(
        ["cmd", "/c", "gradle", "--version"], capture_output=True, text=True)
    if gradle_check.returncode != 0:
        print("❌ Gradle non trouvé. Installez Gradle ou ajoutez le wrapper 'gradlew' au projet.")
        if gradle_check.stderr:
            print(gradle_check.stderr)
        return False

    gradle_version = (
        gradle_check.stdout or gradle_check.stderr or "").strip().splitlines()[0]
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
    print("\n🚀 Lancement des tests...")

    output = subprocess.run(command, capture_output=True,
                            text=True, encoding='utf-8', errors='replace')

    return output.returncode


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
    try:
        angular_command = ["cmd", "/c", "npm", "test"]
        gradlew_cmd = "gradlew.bat" if os.path.exists(
            "gradlew.bat") else "gradlew"
        java_command = ["cmd", "/c", gradlew_cmd, "clean", "test"]
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
