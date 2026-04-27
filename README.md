# RTD-Analyzer-COS

Program do obróbki wyników badań uzyskanych z modeli fizycznych agregatów metalurgicznych COS (krzywe RTD typu F).  
Projekt realizuje wymagania z materiałów w folderze `PDF` i pozwala przejść pełny proces: od wczytania danych pomiarowych do wyznaczenia stref przejściowych 0.2-0.8.

## 1. Cel projektu

Celem projektu było opracowanie aplikacji, która:
- wczytuje dane z eksperymentów modelowych COS z plików CSV,
- umożliwia odrzucenie wskazanych pomiarów od początku serii,
- rysuje krzywe RTD dla wybranych kanałów (wylewów),
- przelicza dane na postać bezwymiarową,
- wyznacza strefę przejściową dla każdego kanału:
  `t_w,0.8 - t_w,0.2`,
- zapisuje wyniki do plików.

## 2. Podstawa merytoryczna

Projekt oparto o wytyczne i opisy metodyczne z katalogu `PDF`, w szczególności:
- `Wytyczne Program COS.pdf`,
- `Krzywa RTD typu F_COS.pdf`,
- `Krzywe RTD czas bezwymiarowy.pdf`,
- `Przeliczanie stężenia znacznika na wartości bezwymiarowe.pdf`.

W analizie zastosowano:
- dane pomiarowe przewodności elektrycznej (µS/cm),
- krok czasowy pomiaru `0.3 s`,
- normalizację stężenia do postaci bezwymiarowej C*,
- granice C* = 0.2 oraz C* = 0.8 do wyznaczenia czasu strefy przejściowej.

## 3. Zakres funkcjonalny aplikacji

### 3.1 Wejście danych
- import pliku `.csv` (separator `;`, liczby z przecinkiem dziesiętnym),
- obsługa kanałów pomiarowych (wylewów) do maks. 6.

### 3.2 Przygotowanie danych
- ręczne odrzucanie wybranej liczby wierszy od początku,
- budowanie osi czasu w sekundach na podstawie interwału (domyślnie `0.3 s`).

### 3.3 Analiza
- wykres surowych danych: `czas [s]` vs `przewodność [µS/cm]`,
- przeliczenie do C* z wyborem sposobu wyznaczania `C∞`:
  - `max` (maksymalna przewodność),
  - `last` (przewodność końcowa),
- wykres C* z opcją dodania granic 0.2 i 0.8,
- obliczenie `t(0.2)`, `t(0.8)` i `Δt = t(0.8) - t(0.2)` (interpolacja liniowa).

### 3.4 Eksport
- zapis CSV:
  - dane surowe po odrzuceniu,
  - dane bezwymiarowe,
  - tabela stref przejściowych,
- zapis wykresu C* do PNG.

## 4. Implementacja techniczna

### 4.1 Technologie
- **Python 3.11+**
- **Streamlit** - interfejs aplikacji
- **Pandas / NumPy** - obróbka danych
- **Matplotlib** - wykresy
- **unittest** - testy logiki

### 4.2 Struktura projektu
- `app.py` - aplikacja web (UI + workflow użytkownika),
- `rtd_analyzer/data_processing.py` - logika obliczeń i walidacji,
- `tests/test_data_processing.py` - testy jednostkowe,
- `Testing/` - przykładowe pliki wejściowe (`TEST1.csv`, `TEST2.csv`),
- `PDF/` - materiały źródłowe i wytyczne.

## 5. Weryfikacja działania

Do sprawdzenia poprawności działania wykorzystano dane z `Testing/` oraz testy jednostkowe funkcji:
- przygotowania okna eksperymentu,
- normalizacji do C*,
- wyznaczania strefy przejściowej.

## 6. Uruchomienie lokalne

### Pobranie projektu

```bash
git clone https://github.com/Mateusz-Latka/RTD-Analyzer-COS.git
cd RTD-Analyzer-COS
```

### Instalacja i start

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
streamlit run app.py
```

Po uruchomieniu aplikacja jest dostępna lokalnie pod adresem wskazanym przez Streamlit.

### Tryb offline

Program działa offline po lokalnej instalacji zależności. Do codziennej pracy nie wymaga połączenia z internetem (internet jest potrzebny tylko do jednorazowego pobrania repozytorium i pakietów Python).

## 7. Uruchomienie w Dockerze

Projekt zawiera `Dockerfile` uruchamiający aplikację na porcie `8080`.

```bash
docker build -t rtd-analyzer-cos .
docker run --rm -p 8080:8080 rtd-analyzer-cos
```

Aplikacja będzie dostępna pod `http://localhost:8080`.

## 8. Wdrożenie na DigitalOcean (App Platform)

1. Umieść repozytorium na GitHubie.
2. W DigitalOcean wybierz **Create -> Apps**.
3. Wskaż repozytorium projektu.
4. App Platform wykryje `Dockerfile`.
5. Ustaw port serwisu na `8080`.
6. Wykonaj deploy i korzystaj z publicznego URL.

## 9. Podsumowanie

Projekt dostarcza kompletną aplikację do cyfrowej obróbki danych RTD typu F dla modelu COS:
- zgodną z przekazanymi wytycznymi,
- gotową do użycia laboratoryjnego,
- przygotowaną do uruchamiania lokalnie i kontenerowo.
