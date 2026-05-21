import argostranslate.package


LANGUAGES = {
    "ar",
    "bg",
    "cs",
    "da",
    "de",
    "el",
    "en",
    "es",
    "et",
    "fi",
    "fr",
    "hi",
    "hr",
    "hu",
    "id",
    "it",
    "ja",
    "ko",
    "lt",
    "lv",
    "nl",
    "pl",
    "pt",
    "ro",
    "ru",
    "sk",
    "sl",
    "sv",
    "tr",
    "uk",
    "vi",
}


def main() -> None:
    argostranslate.package.update_package_index()
    available = argostranslate.package.get_available_packages()
    pairs = sorted(
        {
            (package.from_code, package.to_code)
            for package in available
            if package.from_code in LANGUAGES
            and package.to_code in LANGUAGES
            and "en" in {package.from_code, package.to_code}
        }
    )
    for source, target in pairs:
        package = next((p for p in available if p.from_code == source and p.to_code == target), None)
        if package is None:
            print(f"Skipping missing Argos model: {source}->{target}")
            continue
        print(f"Installing Argos model: {source}->{target}")
        path = package.download()
        argostranslate.package.install_from_path(path)


if __name__ == "__main__":
    main()
