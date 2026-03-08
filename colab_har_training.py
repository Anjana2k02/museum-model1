import os
import zipfile
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, VotingClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


LABEL_MAP = {
    1: "WALKING",
    4: "SITTING",
    5: "STANDING",
}
TARGET_LABELS = sorted(LABEL_MAP.keys())


def resolve_dataset_dir(dataset_path: str | Path) -> Path:
    dataset_path = Path(dataset_path)
    candidates = [
        dataset_path,
        dataset_path / "UCI HAR Dataset",
    ]
    for candidate in candidates:
        if (candidate / "train" / "X_train.txt").exists() and (candidate / "test" / "X_test.txt").exists():
            return candidate
    raise FileNotFoundError(
        f"Could not find a valid UCI HAR Dataset under: {dataset_path}"
    )


# Optional helper if you still want to work from a zip file.
def extract_uploaded_zip(zip_path: str, extract_to: str = "/content") -> Path:
    zip_path = Path(zip_path)
    extract_to = Path(extract_to)
    with zipfile.ZipFile(zip_path, "r") as archive:
        archive.extractall(extract_to)

    candidates = [
        extract_to / "UCI HAR Dataset",
        extract_to / zip_path.stem,
        extract_to,
    ]
    for candidate in candidates:
        if (candidate / "train" / "X_train.txt").exists():
            return candidate
    raise FileNotFoundError("Could not find the extracted UCI HAR Dataset folder.")


def mount_drive_and_resolve_dataset(folder_path: str) -> Path:
    from google.colab import drive

    drive.mount("/content/drive", force_remount=False)

    candidate_paths = [Path(folder_path)]
    if "My Drive" in folder_path:
        candidate_paths.append(Path(folder_path.replace("My Drive", "MyDrive")))
    elif "MyDrive" in folder_path:
        candidate_paths.append(Path(folder_path.replace("MyDrive", "My Drive")))

    for candidate_path in candidate_paths:
        if candidate_path.exists():
            return resolve_dataset_dir(candidate_path)

    checked_paths = "\n".join(str(path) for path in candidate_paths)
    raise FileNotFoundError(
        "Google Drive folder not found. Checked:\n"
        f"{checked_paths}\n"
        "Verify the folder name and whether it is under MyDrive."
    )


def load_split(dataset_dir: Path, split: str):
    x_path = dataset_dir / split / f"X_{split}.txt"
    y_path = dataset_dir / split / f"y_{split}.txt"
    subject_path = dataset_dir / split / f"subject_{split}.txt"

    X = pd.read_csv(x_path, delim_whitespace=True, header=None)
    y = pd.read_csv(y_path, header=None).iloc[:, 0]
    subjects = pd.read_csv(subject_path, header=None).iloc[:, 0]

    mask = y.isin(TARGET_LABELS)
    X = X.loc[mask].reset_index(drop=True)
    y = y.loc[mask].map(LABEL_MAP).reset_index(drop=True)
    subjects = subjects.loc[mask].reset_index(drop=True)
    return X, y, subjects


def load_feature_names(dataset_dir: Path):
    features_path = dataset_dir / "features.txt"
    features = pd.read_csv(features_path, delim_whitespace=True, header=None, names=["index", "feature"])
    return features["feature"].tolist()


def build_model(random_state: int = 42):
    rf = RandomForestClassifier(
        n_estimators=500,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        class_weight="balanced_subsample",
        n_jobs=-1,
        random_state=random_state,
    )

    et = ExtraTreesClassifier(
        n_estimators=500,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        class_weight="balanced",
        n_jobs=-1,
        random_state=random_state,
    )

    ensemble = VotingClassifier(
        estimators=[("rf", rf), ("et", et)],
        voting="soft",
        n_jobs=-1,
    )

    return Pipeline([
        ("scaler", StandardScaler()),
        ("model", ensemble),
    ])


def train_and_evaluate(dataset_dir: Path, output_path: str | Path = "/content/har_position_model.joblib"):
    feature_names = load_feature_names(dataset_dir)
    X_train, y_train, subjects_train = load_split(dataset_dir, "train")
    X_test, y_test, subjects_test = load_split(dataset_dir, "test")

    X_train.columns = feature_names
    X_test.columns = feature_names

    model = build_model()
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)
    report = classification_report(y_test, predictions)
    matrix = confusion_matrix(y_test, predictions, labels=list(LABEL_MAP.values()))

    print("Dataset directory:", dataset_dir)
    print("Train shape:", X_train.shape)
    print("Test shape:", X_test.shape)
    print("Train class counts:")
    print(y_train.value_counts().sort_index())
    print("Test class counts:")
    print(y_test.value_counts().sort_index())
    print("Unique train subjects:", subjects_train.nunique())
    print("Unique test subjects:", subjects_test.nunique())
    print(f"\nAccuracy: {accuracy:.4f}")
    print("\nClassification report:\n")
    print(report)
    print("Confusion matrix (rows=true, cols=pred):")
    print(pd.DataFrame(matrix, index=LABEL_MAP.values(), columns=LABEL_MAP.values()))

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_path)
    print(f"\nSaved model to {output_path}")

    return model


if __name__ == "__main__":
    drive_folder = "/content/drive/MyDrive/Data Sciense/research-module"
    dataset_dir = mount_drive_and_resolve_dataset(drive_folder)
    model_path = dataset_dir / "har_position_model.joblib"

    print(f"Using dataset from: {dataset_dir}")
    train_and_evaluate(dataset_dir, output_path=model_path)
