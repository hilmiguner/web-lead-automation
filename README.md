# Web Lead Automation

Yerel işletmeler arasından **web sitesi olmayan veya dijital varlığı zayıf potansiyel müşterileri bulmak**, önceliklendirmek, AI ile hızlı demo web sitesi hazırlamak ve satış sürecini takip etmek için geliştirilen yarı otomatik bir araç.

Bu projenin amacı kusursuz bir SaaS geliştirmek değil; **olabildiğince hızlı şekilde gerçek müşteri adayları bulup web sitesi satmaya başlamaktır.**

## MVP Akışı

```text
Bölge + sektör seç
        ↓
İşletmeleri bul
        ↓
Web sitesi olmayanları filtrele
        ↓
Lead score hesapla
        ↓
En iyi adayları göster
        ↓
CRM durumunu kaydet
        ↓
AI ile kişiselleştirilmiş demo site oluştur
        ↓
Paylaşılabilir preview al
        ↓
Demo linkli satış mesajı hazırla
        ↓
İletişime geç ve sonucu takip et
```

Başlangıç bölgesi: **Gemlik → Bursa → yakın ilçeler**.

## Şu Anda Çalışan Akış

Mevcut sürümde Streamlit dashboard üzerinden:

1. Bölge girilir.
2. Hazır sektör seçilir veya özel sektör yazılır.
3. `Lead Ara` butonuna basılır.
4. Google Places API (New) üzerinden işletmeler aranır.
5. Google Places'ta website bilgisi listelenmeyen işletmeler ayrılır.
6. Lead'ler 0–100 arası açıklanabilir skorla sıralanır.
7. SQLite CRM geçmişi sonuçlara eklenir.
8. Sonuç tablosunda işletme, skor, telefon, rating, yorum, CRM durumu, adres ve Maps linki görülür.

CRM durumları:

```text
NEW
CONTACTED
INTERESTED
WON
LOST
```

## Teknoloji

| Katman | Teknoloji |
|---|---|
| Dil | Python 3.11+ |
| Arayüz | Streamlit 1.61+ |
| Veri | SQLite |
| İşletme keşfi | Google Places API (New) |
| HTTP | httpx |
| Konfigürasyon | pydantic-settings |
| Test | pytest + Streamlit AppTest |
| CI | GitHub Actions |

MVP doğrulandıktan sonra ihtiyaç oluşursa ayrı API, PostgreSQL veya daha gelişmiş frontend mimarisine geçilebilir.

## Proje Yapısı

```text
web-lead-automation/
├── .github/
│   └── workflows/
│       └── ci.yml
├── app.py
├── src/
│   └── web_lead_automation/
│       ├── __init__.py
│       ├── __main__.py
│       ├── config.py
│       ├── logging_config.py
│       ├── streamlit_app.py
│       ├── ui_models.py
│       ├── services/
│       │   ├── lead_finder.py
│       │   ├── lead_history.py
│       │   ├── places.py
│       │   ├── scoring.py
│       │   └── website_filter.py
│       └── storage/
│           └── crm.py
├── tests/
├── .env.example
├── .gitignore
├── pyproject.toml
├── README.md
└── ROADMAP.md
```

## Kurulum

Windows PowerShell:

```powershell
git clone https://github.com/hilmiguner/web-lead-automation.git
cd web-lead-automation

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -e ".[dev]"

Copy-Item .env.example .env
```

`.env` dosyasını açıp Google Places API anahtarını gir:

```env
APP_ENV=development
LOG_LEVEL=INFO
GOOGLE_PLACES_API_KEY=YOUR_API_KEY
GOOGLE_PLACES_TIMEOUT_SECONDS=10
GOOGLE_PLACES_PAGE_SIZE=20
LEAD_DB_PATH=data/leads.sqlite3
```

Gerçek API anahtarları ve secret değerler GitHub'a commit edilmemelidir.

## Dashboard'u Çalıştır

```powershell
streamlit run app.py
```

Tarayıcı otomatik açılmazsa terminalde Streamlit'in gösterdiği local adres açılır.

API key tanımlı değilse dashboard yine açılır ancak gerçek işletme araması yapılamaz ve ekranda uyarı gösterilir.

## Testler

```powershell
pytest
```

CI; servis katmanı, SQLite CRM, scoring, website filtresi ve Streamlit dashboard smoke testlerini çalıştırır.

Foundation smoke test:

```powershell
python -m web_lead_automation
```

## Lead Scoring v1

İlk sürüm deterministik ve açıklanabilir bir puanlama kullanır:

| Sinyal | Maksimum Puan |
|---|---:|
| Google Places'ta website listelenmiyor | 40 |
| Telefon mevcut | 15 |
| Yorum hacmi | 20 |
| Rating | 15 |
| Hedef işletme türü | 10 |
| **Toplam** | **100** |

Puanlama gerçek satış sonuçlarına göre güncellenecektir. Amaç teorik olarak mükemmel skor değil, **hangi işletmenin önce aranması gerektiğini söyleyen pratik bir sıralama** üretmektir.

## Website Durumu Hakkında

Google Places'ta `websiteUri` alanının bulunmaması, işletmenin internetin hiçbir yerinde sitesi olmadığını matematiksel olarak kanıtlamaz. Bu nedenle uygulama bunu **"Google Places'ta website listelenmiyor"** şeklinde ele alır.

Belirsiz veya bozuk website verileri website'siz lead listesine dahil edilmez.

## CRM ve Lead Geçmişi

SQLite içinde kalıcı olarak temel satış pipeline bilgileri tutulur:

- Google Place ID
- CRM status
- kullanıcı notu
- ilk görülme tarihi
- son güncelleme tarihi

Aynı Place ID tekrar bulunduğunda duplicate kayıt oluşturulmaz. Mevcut status ve not korunur; dashboard lead'in daha önce görülüp görülmediğini gösterebilir.

## AI Demo Website Yaklaşımı

MVP'de AI'ın her lead için sıfırdan serbest biçimde uygulama kodu yazması hedeflenmez. Daha hızlı ve güvenilir yöntem kullanılacaktır:

```text
Lead verisi
   ↓
AI içerik + tema önerisi
   ↓
Test edilmiş landing page template
   ↓
Kişiselleştirilmiş demo
   ↓
Preview linki
```

AI, doğrulanmamış işletme bilgilerini gerçekmiş gibi üretmemelidir. İlk hedef, bir lead için **5 dakikanın altında insan müdahalesiyle** satışta kullanılabilecek demo hazırlamaktır.

## İlk Satış Modeli

Başlangıç teklifi yaklaşık **4.990–5.000 TL** seviyesinde test edilebilir:

- Tek sayfalık modern web sitesi
- Mobil uyumlu tasarım
- WhatsApp iletişim butonu
- Google Maps
- Hizmetler / işletme bilgileri
- Temel SEO
- Yayına alma

Gerçek satış sonuçlarından sonra fiyat ve paketler yeniden değerlendirilecektir.

## MVP Dışında Tutulanlar

İlk satışları geciktirecek özellikler ihtiyaç oluşana kadar ertelenir:

- Tam kapsamlı SaaS mimarisi
- Kullanıcı üyelik sistemi
- Multi-tenancy / RBAC
- Ödeme altyapısı
- PostgreSQL migration
- Mikroservisler
- Kubernetes
- Mobil uygulama
- Tam otonom WhatsApp / e-posta gönderimi
- Gelişmiş multi-agent orkestrasyonu

## Başarı Kriteri

MVP'nin başarı kriteri kod miktarı değildir. Sistem:

1. Gerçek işletmeleri bulabilmeli.
2. Web sitesi olmayan lead'leri ayıklayabilmeli.
3. Her gün aranabilecek kaliteli bir lead listesi çıkarabilmeli.
4. Lead durumlarını takip edebilmeli.
5. Lead için hızlı demo hazırlayabilmeli.
6. Demo linkli satış mesajı oluşturabilmeli.
7. İlk ücretli müşterinin kazanılmasına yardımcı olabilmeli.

Geliştirme sırası ve MVP stop point için [ROADMAP.md](ROADMAP.md) dosyasına bakın.
