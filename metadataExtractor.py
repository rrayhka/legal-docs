import pypdf
import os
import re
import json
import asyncio
import aiofiles
from typing import (
    List,
    Dict,
    Any,
    Optional,
)
from pydantic import BaseModel, Field

class Terdakwa(BaseModel):
    nama_lengkap: Optional[str] = None
    tempat_lahir: Optional[str] = None
    umur: Optional[str] = None
    jenis_kelamin: Optional[str] = None
    kebangsaan: Optional[str] = None
    tempat_tinggal: Optional[str] = None
    agama: Optional[str] = None
    pekerjaan: Optional[str] = None

class TuntutanPidana(BaseModel):
    tuntutan_pidana: str

class ExtractedEntities(BaseModel):
    nomor_putusan: Optional[str] = Field(None, alias="Nomor Putusan")
    tanggal_putusan: Optional[str] = Field(None, alias="Tanggal Putusan")
    informasi_terdakwa: Optional[List[Terdakwa]] = Field(None, alias="Informasi Terdakwa")
    related_pasal: Optional[List[str]] = Field(None, alias="Related Pasal")
    tuntutan_pidana: Optional[str] = Field(None, alias="Tuntutan Pidana")
    tuntutan_hukuman: Optional[str] = Field(None, alias="Tuntutan Hukuman")
    putusan_pidana: Optional[str] = Field(None, alias="Putusan Pidana")
    putusan_hukuman: Optional[str] = Field(None, alias="Putusan Hukuman")
    hakim_ketua: Optional[str] = Field(None, alias="Hakim Ketua")
    hakim_anggota: Optional[str] = Field(None, alias="Hakim Anggota")
    panitera: Optional[str] = Field(None, alias="Panitera")
    
    class Config:
        populate_by_name = True
        json_encoders = {
            set: list
        }

class MetadataExtractorBSus:
    def __init__(self):
        self.content = self

    def nomorPutusan(self) -> str:
        """
        Mengekstrak Nomor Putusan dari teks dokumen.
        Args:
            content (str): Konten teks yang berisi nomor putusan.
        Returns:
            str: Nomor putusan yang ditemukan, atau None jika tidak ditemukan.
        """
        pattern = re.compile(
            r"P\s+U\s+T\s+U\s+S\s+A\s+N\s+(?:\n\s*)?Nomor\s+(\d{1,3}/Pid\.(?:B|Sus)/\d{4}/PN\s+\w+)",
            re.MULTILINE
        )
        match = pattern.search(self.content)
        if match:
            return match.group(1)
        return None

    def dataTerdakwa(self) -> List[Dict[str, Any]]:
        """
        Mengekstrak informasi terdakwa dan return sebagai list of dictionaries.
        Args:
            content (str): Konten teks yang berisi informasi terdakwa.
        Returns:
            List[Dict[str, Any]]: List of dictionaries yang berisi informasi terdakwa.
            - Nama: Nama terdakwa
            - Tempat Lahir: Tempat lahir terdakwa
            - Umur: Umur terdakwa
            - Tempat Tinggal: Tempat tinggal terdakwa
            - Pekerjaan: Pekerjaan terdakwa
            - Agama: Agama terdakwa
        """   
        terdakwa_pattern = re.compile(
            r"(?:T\s*erdakwa\s*\d*\s*\d*\.\s*)?"
            r"(?:\d+\.\s*)?Nama\s*lengkap\s*:?\s*(?P<nama_lengkap>[^;]+);\s*"
            r"(?:\d+\.\s*)?Tempat\s*lahir\s*:?\s*(?P<tempat_lahir>[^;]+);\s*"
            r"(?:\d+\.\s*)?Umur/Tanggal\s*lahir\s*:?\s*(?P<umur>[^;]+);\s*"
            r"(?:\d+\.\s*)?Jenis\s*kelamin\s*:?\s*(?P<jenis_kelamin>[^;]+);\s*"
            r"(?:\d+\.\s*)?Kebangsaan\s*:?\s*(?P<kebangsaan>[^;]+);\s*"
            r"(?:\d+\.\s*)?Tempat\s*tinggal\s*:?\s*(?P<tempat_tinggal>[^;]+);\s*"
            r"(?:\d+\.\s*)?Agama\s*:?\s*(?P<agama>[^;]+);\s*"
            r"(?:\d+\.\s*)?Pekerjaan\s*:?\s*(?P<pekerjaan>[^;]+)[.;]",
            re.IGNORECASE
        )

        results = []
        for match in terdakwa_pattern.finditer(self.content):
            data = match.groupdict()
            cleaned_data = {key: value.strip() for key, value in data.items()}
            results.append(cleaned_data)
            return results
        return None

    def tanggalPutusan(self) -> str:
        """
        Mengekstrak tanggal putusan dari dokumen.
        """

        match = re.search(r"Demikianlah\s+diputuskan.*?pada\s+hari\s+(.+?)(?:,\s*)?oleh\s+kami", self.content, re.IGNORECASE | re.DOTALL)
        if match:
            tanggal_putusan = match.group(1).strip()
            return tanggal_putusan
        return None
    
    def tuntutanPidana(self) -> str:
        """
        Mengekstrak informasi tuntutan pidana dari dokumen.
        Args:
            content (str): Konten teks yang berisi informasi tuntutan pidana.
        Returns:
            str: Teks yang berisi informasi tuntutan pidana.
        """
        pattern = re.compile(
            r"(?:T\s*untutan\s*pidana\s*\d*\s*\d*\.\s*)?"
            r"(?:\d+\.\s*)?Tuntutan\s*pidana\s*:?\s*(?P<tuntutan_pidana>[^;]+);",
            re.IGNORECASE
        )

        results = []
        for match in pattern.finditer(self.content):
            data = match.groupdict()
            cleaned_data = {key: value.strip() for key, value in data.items()}
            results.append(cleaned_data)
            return results
        return None
    
    def normalizedPasal(self, pasal: str) -> str:
        """
        Normalisasi teks pasal untuk konsistensi.
        Menghapus spasi berlebih, mengubah ke huruf kecil,
        dan mengganti istilah tertentu.
        Args:
            pasal (str): Teks pasal yang akan dinormalisasi.
        Returns:
            str: Teks pasal yang telah dinormalisasi.
        """

        pasal = re.sub(r'\s+', ' ', pasal.lower())
        pasal = pasal.replace('kitab undang - undang hukum pidana', 'kuhp')
        pasal = pasal.replace('kitab undang-undang hukum pidana', 'kuhp')
        pasal = pasal.replace('jo.', 'jo')
        pasal = pasal.replace('junctor', 'jo')
        return pasal.strip()
    
    def relatedPasal(self) -> List[str]:
        """
        Mengekstrak pasal terkait dari teks dokumen.
        Menggunakan regex untuk menemukan pola pasal, ayat, dan referensi Jo.
        Mengembalikan daftar pasal yang telah dinormalisasi.
        Args:
            content (str): Konten teks yang berisi informasi pasal.
        Returns:
            list: Daftar pasal yang telah dinormalisasi.
        """
        pattern = r'''(?ix)
            pasal\s+\d+                                   # Pasal 378
            (?:\s+ayat\s+\(?\d+\)?                        # ayat (1)
                (?:\s*,\s*ayat\s+\(?\d+\)?)*              # , ayat (2)
                (?:\s*(?:dan|,)\s*ayat\s+\(?\d+\)?)?      # dan ayat (3)
            )?
            (?:\s+ke-?\d+)?                               # ke-1
            (?:\s+UU\s+RI\s+No\.\s*\d+\s*Tahun\s*\d+)?    # UU RI No. 17 Tahun 2023
            (?:\s+(?:KUHP|Kitab\s+Undang[\s-]*Undang\s+Hukum\s+Pidana))?
            (?:
                \s+(?:Jo\.?|Juncto)\s+Pasal\s+\d+         # Jo. Pasal 55
                (?:\s+ayat\s+\(?\d+\)?                    # ayat (1)
                    (?:\s*,\s*ayat\s+\(?\d+\)?)*          # , ayat (2)
                    (?:\s*(?:dan|,)\s*ayat\s+\(?\d+\)?)?  # dan ayat (3)
                )?
                (?:\s+ke-?\d+)?                           # ke-1
                (?:\s+(?:KUHP|Kitab\s+Undang[\s-]*Undang\s+Hukum\s+Pidana))?
            )*
        '''
        matches = re.findall(pattern, self.content, re.MULTILINE)
        return list(dict.fromkeys(m.strip() for m in matches if m.strip()))
    

    def tuntutanHukuman(self) -> str:
        """
        Mengekstrak durasi tuntutan hukuman dari teks dokumen.
        Mencari frasa yang mengandung "dengan hukuman penjara" dan mengambil durasi setelahnya.
        Contoh durasi yang diharapkan: "5 (lima) tahun", "10 tahun 2 bulan", "8 bulan".

        Args:
            content (str): Konten teks yang berisi informasi tuntutan hukuman.
        Returns:
            str: Durasi tuntutan hukuman yang ditemukan, atau None jika tidak ditemukan.
        """
        block = re.search(r'pembacaan tuntutan pidana.*?(?=\n\n|\Z)', self.content, re.IGNORECASE | re.DOTALL)
        if not block:
            return None

        # Ambil frasa durasi setelah "dengan pidana penjara"
        match = re.search(
            r'dengan pidana penjara\s+(.*?)(?:[.,;\n]|dikurangi|dengan perintah)',
            block.group(0),
            re.IGNORECASE | re.DOTALL
        )

        if match:
            durasi = match.group(1).strip()
            return durasi  # contoh: "5 (lima) tahun", "10 tahun 2 bulan", "8 bulan"
        return None
    
    def putusanPidana(self) -> str:
        """
        Mengekstrak durasi putusan pidana dari teks dokumen.
        Mencari frasa yang mengandung "Menjatuhkan pidana" dan mengambil durasi setelahnya.
        Contoh durasi yang diharapkan: "4 (empat) tahun", "5 tahun 6 bulan", "3 bulan".
        Args:
            content (str): Konten teks yang berisi informasi putusan pidana.
        Returns:
            str: Durasi putusan pidana yang ditemukan, atau None jika tidak ditemukan.
        """

        block = re.search(r'MENGADILI:(.*?)(?=\n\n|\Z)', self.content, re.IGNORECASE | re.DOTALL)
        if not block:
            return None

        match = re.search(
            r'Menjatuhkan pidana.*?dengan pidana penjara\s+selama\s+(.*?)(?:[.,;\n]|dan|dikurangi)',
            block.group(1),
            re.IGNORECASE | re.DOTALL
        )

        if match:
            durasi = match.group(1).strip()
            return durasi  # contoh: "4 (empat) tahun", "5 tahun 6 bulan"
        return None
    
    def putusanHukuman(self) -> str:
        """
        Mengekstrak informasi putusan hukuman dari teks dokumen.
        Mencari blok teks yang dimulai dengan "MENGADILI:" dan berakhir sebelum "Demikianlah diputuskan".
        Args:
            content (str): Konten teks yang berisi informasi putusan hukuman.
        Returns:
            str: Teks putusan hukuman yang ditemukan, atau None jika tidak ditemukan.
        """
        match = re.search(r'MENGADILI:(.*?)(?=Demikianlah diputuskan)', self.content, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
    
    def hakimKetua(self) -> str:
        """
        Mengekstrak nama Hakim Ketua dari teks.
        Mengembalikan string nama jika ditemukan, None jika tidak.
        """
        pattern = re.search(
            r"oleh\s+kami,?\s*(.*?)(?=sebagai\s+Hakim\s+Ketua)",
            self.content,
            re.IGNORECASE | re.DOTALL
        )
        
        if pattern:
            nama = pattern.group(1).strip()
            # Hapus pemisah jika ada lebih dari satu nama
            nama = re.split(r",\s*(dan|masing-masing|sebagai)", nama)[0]
            return nama.strip(", ")
        return None
    
    def hakimAnggota(self) -> str:
        """
        Mengekstrak bagian teks yang berisi nama-nama Hakim Anggota,
        yaitu teks setelah 'Hakim Ketua' dan sebelum frasa opsional
        'masing-masing sebagai Hakim Anggota'.
        
        Returns:
            String mentah dari bagian yang cocok.
        """
        # Regex untuk mengekstrak teks antara 'Hakim Ketua' hingga sebelum frasa opsional
        pattern = re.search(
            r"sebagai\s+Hakim\s+Ketua[,]?\s+(.*?)(?=masing-masing\s+sebagai\s+Hakim\s+Anggota|$)",
            self.content,
            re.IGNORECASE | re.DOTALL
        )

        if pattern:
            result = pattern.group(1).replace('\n', ' dan ').strip()
            return re.sub(r'\s+', ' ', result)
        return None
    
    def paniteraPengganti(self) -> str:
        """
        Mengekstrak nama Panitera dari teks, dengan atau tanpa kata 'sebagai'.
        Mengembalikan string nama jika ditemukan, None jika tidak.
        """
        pattern = re.search(
            r"dibantu\s+oleh\s+(.*?)(?:\s+sebagai)?\s+Panitera",
            self.content,
            re.IGNORECASE | re.DOTALL
        )
        
        if pattern:
            nama = pattern.group(1).strip().strip(", ")
            return nama
        
        return None

type_document = "bsus"

if type_document == "bsus": 
    extract_entities = MetadataExtractorBSus()
else:
    raise ValueError("Unsupported document type. Please use 'bsus' for this extractor.")

async def readFile(file_path: str) -> str:
    async with aiofiles.open(file_path, "r", encoding="utf-8", errors="replace") as file:
        return await file.read()

async def extractEntities(file_path: str) -> Dict[str, Any]:
    """
    Extracts the entity name from a file path using a regular expression.
    The function reads the content of the file, applies a regex pattern to find
    the entity name, and returns the matched entity.
    Args:
    file_path (str): The path of txt file file.

    Returns:
    Dict[str, Any]: JSON compatible dictionary with extracted entities.
    """
    entities = {
        "Nomor Putusan": None,
        "Tanggal Putusan": None,
        "Informasi Terdakwa": None,
        "Related Pasal": None,
        "Tuntutan Pidana": None,
        "Tuntutan Hukuman": None,
        "Putusan Pidana": None,
        "Putusan Hukuman": None,
        "Hakim Ketua": None,
        "Hakim Anggota": None,
        "Panitera": None,
    }
    extract_entities.content = await readFile(file_path)

    nomor_putusan = extract_entities.nomorPutusan()
    if nomor_putusan: entities["Nomor Putusan"] = nomor_putusan

    tanggal_putusan = extract_entities.tanggalPutusan()
    if tanggal_putusan: entities["Tanggal Putusan"] = tanggal_putusan    
    
    data_terdakwa = extract_entities.dataTerdakwa()
    if data_terdakwa: entities["Informasi Terdakwa"] = data_terdakwa
    
    tuntutan_pidana = extract_entities.tuntutanPidana()
    if tuntutan_pidana: entities["Tuntutan Pidana"] = tuntutan_pidana[0]["tuntutan_pidana"]

    related_pasal_matches = extract_entities.relatedPasal()
    if related_pasal_matches: entities["Related Pasal"] = related_pasal_matches
    
    tuntutan_hukuman = extract_entities.tuntutanHukuman()
    if tuntutan_hukuman: entities["Tuntutan Hukuman"] = tuntutan_hukuman

    putusan_pidana = extract_entities.putusanPidana()
    if putusan_pidana: entities["Putusan Pidana"] = putusan_pidana    

    putusan_hukuman = extract_entities.putusanHukuman()
    if putusan_hukuman: entities["Putusan Hukuman"] = putusan_hukuman

    hakim_ketua = extract_entities.hakimKetua()
    if hakim_ketua: entities["Hakim Ketua"] = hakim_ketua

    hakim_anggota = extract_entities.hakimAnggota()
    if hakim_anggota: entities["Hakim Anggota"] = hakim_anggota

    panitera = extract_entities.paniteraPengganti()
    if panitera: entities["Panitera"] = panitera    
    
    # Validate using Pydantic model
    validated_entities = ExtractedEntities(**entities)
    return validated_entities.model_dump(by_alias=True)

async def main():
    print("Metadata Extractor for BSus")
    file_path = "samples/final_output_asli.txt"
    extracted_entities = await extractEntities(file_path)
    print("Hasil ekstraksi:")
    print(json.dumps(extracted_entities, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())