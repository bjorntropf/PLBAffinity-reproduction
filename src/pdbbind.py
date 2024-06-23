import os
import shutil
import tarfile
from enum import Enum

import requests
from tqdm import tqdm


class Type(Enum):
    ACTIVITIES = "Activities"
    LIGANDS = "Ligands"
    POCKETS = "Pockets"
    PROTEINS = "Proteins"


# TODO: Support more datasets
BASE_URL = "http://www.pdbbind.org.cn/download/"
DATASETS = {
    2007: {
        "casf": ["CASF-2007.tar.gz"],
        "refined": ["pdbbind_v2007.tar.gz"],
    },
    2013: {
        "casf": ["CASF-2013-updated.tar.gz", "PDBbind2013-txt-format.tar"],
        "refined": ["pdbbind_v2013_refined_set.tar.gz"],
    },
    2016: {
        "casf": ["CASF-2016.tar.gz"],
        "refined": ["pdbbind_v2016_refined.tar.gz"],
    },
    2019: {
        "refined": ["pdbbind_v2019_refined.tar.gz"],
    },
    2020: {
        "refined": ["PDBbind_v2020_refined.tar.gz"],
    },
}

CASF_2007_LIGAND_PATH = os.path.join("CASF", "ligand", "docking")
CASF_2007_PROTEIN_PATH = os.path.join("CASF", "protein")
PDBBIND_YEAR_PATH = {
    2007: "v2007",
    2013: "v2013-refined",
    2016: "refined-set",
    2019: "refined-set",
    2020: "refined-set",
}
PDBBIND_INDEX_FILE = {
    2007: "INDEX.2007.refined.data",
    2013: os.path.join("..", "..", "PDBbind2013-txt-format", "INDEX_refined_data.2013"),
    2016: os.path.join("index", "INDEX_refined_data.2016"),
    2019: os.path.join("index", "INDEX_refined_data.2019"),
    2020: os.path.join("index", "INDEX_refined_data.2020"),
}


class PDBbind:
    def __init__(self, dataset_directory, username, password):
        self.directory = dataset_directory
        self._make_directory(self.directory)
        self.auth = (username, password)

    def prepare(self, year, _set):
        for subset in self._get_dataset(year, _set):
            filename, url = subset
            filepath = self._download_dataset(filename, url)
            self._extract_dataset(filepath)

    def _get_dataset(self, year, _set):
        if year not in DATASETS:
            raise ValueError(f"Invalid PDBbind dataset: {year}")

        if _set not in DATASETS[year]:
            raise ValueError(f"Invalid PDBbind dataset: {_set}")

        urls = []
        for filename in DATASETS[year][_set]:
            url = BASE_URL + filename
            urls.append((url.split("/")[-1], url))
        return urls

    def _make_directory(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    def _download_dataset(self, filename, url):
        filepath = os.path.join(self.directory, filename)
        if os.path.exists(filepath):
            return filepath

        print(f"Downloading {url}")

        part_filepath = f"{filepath}.part"
        self._download_file(part_filepath, url)

        if os.path.exists(part_filepath):
            shutil.move(part_filepath, filepath)

        return filepath

    def _download_file(self, filepath, url):
        file_exists = os.path.exists(filepath)
        file_size = os.path.getsize(filepath) if file_exists else 0
        headers = {"Range": f"bytes={file_size}-"} if file_exists else {}

        response = requests.get(
            url, auth=self.auth, headers=headers, stream=True, timeout=60
        )
        if response.status_code not in [200, 206]:
            raise requests.exceptions.HTTPError(
                f"Error: {response.status_code} {response.reason}"
            )

        self._download_to_file(filepath, file_size, response)

    def _download_to_file(self, filepath, file_size, response):
        chunk_size = 1024 * 1024
        mode = "ab" if file_size > 0 else "wb"
        remaining = int(response.headers.get("content-length", 0))
        total = file_size + remaining

        with open(filepath, mode) as f:  # pylint: disable=W1514
            with tqdm(total=total, unit="iB", unit_scale=True) as t:
                if file_size > 0:
                    t.update(file_size)

                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        t.update(len(chunk))

    def _extract_dataset(self, filepath):
        destination = filepath.removesuffix(".gz").removesuffix(".tar")
        if os.path.exists(destination):
            return True

        print(f"Extracting {filepath}")
        mode = "r:gz" if filepath.endswith(".gz") else "r"
        with tarfile.open(filepath, mode) as tar:
            total = len(tar.getmembers())
            for member in tqdm(iterable=tar.getmembers(), total=total):
                tar.extract(member, path=destination)

    def activities(self, year, _set):
        return self._get_filepaths(year, _set, Type.ACTIVITIES, (0, 3))

    def ligands(self, year, _set):
        return self._get_filepaths(year, _set, Type.LIGANDS, ("_ligand", ".mol2"))

    def proteins(self, year, _set):
        return self._get_filepaths(year, _set, Type.PROTEINS, ("_protein", ".pdb"))

    def pockets(self, year, _set):
        return self._get_filepaths(year, _set, Type.POCKETS, ("_pocket", ".pdb"))

    def _get_filepaths(self, year, _set, _type, data):
        filename, _ = self._get_dataset(year, _set)[0]
        dirname = filename.removesuffix(".tar.gz")

        if _set.lower() == "casf":
            if _type == Type.LIGANDS:
                path = os.path.join(dirname, CASF_2007_LIGAND_PATH)
            elif _type == Type.PROTEINS:
                path = os.path.join(dirname, CASF_2007_PROTEIN_PATH)
            else:
                # TODO: Fix error ValueError: Type.LIGANDS are not supported for CASF
                raise ValueError(f"{_type} are not supported for CASF")

            return self._get_filepaths_from_dir(path, data[0], data[1])

        path = os.path.join(dirname, PDBBIND_YEAR_PATH[year])
        index = PDBBIND_INDEX_FILE[year]

        if _type == Type.ACTIVITIES:
            return self._get_tuples_from_index(path, index, data)

        return self._get_filepaths_from_index(path, index, data[0], data[1])

    def _get_filepaths_from_dir(self, directory, suffix, extension):
        fullpath = os.path.join(self.directory, directory)

        filepaths = {}
        for root, _, files in os.walk(fullpath):
            for filename in files:
                if filename.endswith(suffix + extension):
                    name = filename.split(suffix + extension)[0]
                    filepaths[name] = os.path.join(root, filename)

        return filepaths

    def _get_filepaths_from_index(self, directory, index, suffix, extension):
        fullpath = os.path.join(self.directory, directory)

        filepaths = {}
        index_file = os.path.join(fullpath, index)
        for name in self._get_columns_from_index(index_file, [0])[0]:
            filepath = os.path.join(fullpath, name, name + suffix + extension)
            if not os.path.exists(filepath):
                print(f"Filepath not found: {filepath}")
                continue

            filepaths[name] = filepath
        return filepaths

    def _get_tuples_from_index(self, directory, index, zip_columns):
        fullpath = os.path.join(self.directory, directory)

        index_file = os.path.join(fullpath, index)
        columns = self._get_columns_from_index(index_file, zip_columns)

        return list(zip(*columns))

    def _get_columns_from_index(self, filepath, columns, skip_str="#"):
        results = [[] for _ in range(len(columns))]
        with open(filepath, "r", encoding="utf-8") as file:
            for line in file:
                if line.startswith(skip_str):
                    continue

                split_line = line.split()
                if split_line:
                    for i, col_index in enumerate(columns):
                        results[i].append(split_line[col_index])
        return results
