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

## MVP Kapsamı

MVP tamamlandığında kullanıcı:

- Bölge ve sektör girerek işletme arayabilecek.
- Web sitesi bulunan / bulunmayan işletmeleri ayırabilecek.
- Potansiyel müşterileri otomatik puanlayabilecek.
- En değerli lead'leri sıralayabilecek.
- Lead durumunu ve notlarını takip edebilecek.
- Seçilen lead için AI destekli tek sayfalık demo site oluşturabilecek.
- Demo için paylaşılabilir preview alabilecek.
- Demo linkli kişiselleştirilmiş satış mesajı oluşturabilecek.
- Daha önce işlenen işletmelerin tekrar tekrar karşısına çıkmasını engelleyebilecek.

İlk CRM durumları:

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
| Arayüz | Streamlit |
| Veri | SQLite |
| İşletme keşfi | Google Places API (New) |
| HTTP | httpx |
| Konfigürasyon | pydantic-settings |
| Test | pytest |
| CI | GitHub Actions |

MVP doğrulandıktan sonra ihtiyaç oluşursa ayrı API, PostgreSQL veya daha gelişmiş frontend mimarisine geçilebilir.

## Mevcut Proje Yapısı

```text
web-lead-automation/
├── .github/
│   └── workflows/
│       └── ci.yml
├── src/
│   └── web_lead_automation/
│       ├── __init__.py
│       ├── __main__.py
│       ├── config.py
│       └── logging_config.py
├── tests/
│   ├── test_config.py
│   └── test_logging_config.py
├── .env.example
├── .gitignore
├── pyproject.toml
├── README.md
└── ROADMAP.md
```

Yapı geliştirme ilerledikçe servis, veri ve UI katmanlarıyla genişletilecektir.

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

Foundation smoke test:

```powershell
python -m web_lead_automation
```

Testler:

```powershell
pytest
```

Beklenen test sonucu foundation aşamasında:

```text
4 passed
```

## Environment

`.env.example` dosyası local `.env` dosyasına kopyalanır.

```env
APP_ENV=development
LOG_LEVEL=INFO
GOOGLE_PLACES_API_KEY=
LEAD_DB_PATH=data/leads.sqlite3
```

Gerçek API anahtarları ve secret değerler GitHub'a commit edilmemelidir.

## Lead Scoring

İlk sürümde basit ve açıklanabilir bir puanlama kullanılacaktır. Örnek sinyaller:

- Web sitesi bulunmuyor
- Telefon numarası mevcut
- Yüksek Google yorum sayısı
- İyi Google puanı
- İşletme aktif görünüyor
- Seçilen sektör satış açısından değerli
- Daha önce iletişime geçilmemiş

Puanlama gerçek satış sonuçlarına göre güncellenecektir. Amaç teorik olarak mükemmel skor değil, **hangi işletmenin önce aranması gerektiğini söyleyen pratik bir sıralama** üretmektir.

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

## Veri Kullanımı

Harici veri kaynaklarının kullanım ve saklama koşulları dikkate alınacaktır. Kalıcı CRM verisi mümkün olduğunca bizim ürettiğimiz satış bilgileriyle sınırlı tutulacaktır:

- Harici işletme kimliği
- Lead durumu
- Kullanıcı notları
- İletişim geçmişi
- Lead score ve uygulamanın ürettiği metadata
- Demo bağlantısı

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
