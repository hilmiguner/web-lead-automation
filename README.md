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

## Mevcut Özellikler

- Google Places API (New) ile sektör + bölge araması
- Web sitesi listelenen / listelenmeyen işletme ayrımı
- Açıklanabilir 0–100 lead scoring
- SQLite tabanlı minimal CRM
- Duplicate Place ID kontrolü
- Lead geçmişi: yeni, daha önce görülmüş, iletişime geçilmiş, WON / LOST
- Streamlit üzerinden bölge ve sektör seçimi
- `Lead Ara` aksiyonu
- Skora göre sıralı sonuç tablosu
- Telefon, rating, yorum, adres ve Google Maps linki
- En yüksek skorlu lead için skor nedenleri

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

`.env` içinde Google Places anahtarını tanımla:

```env
APP_ENV=development
LOG_LEVEL=INFO
GOOGLE_PLACES_API_KEY=your_api_key_here
LEAD_DB_PATH=data/leads.sqlite3
```

Gerçek API anahtarları ve secret değerler GitHub'a commit edilmemelidir.

## Dashboard'u Çalıştırma

```powershell
streamlit run src/web_lead_automation/dashboard.py
```

Tarayıcıda açılan ekranda:

1. Bölge seç.
2. Sektör seç.
3. İstersen özel bölge / sektör gir.
4. `Lead Ara` butonuna bas.
5. Web sitesi Google Places'ta listelenmeyen işletmeleri skor sırasıyla incele.

İlk kullanım için önerilen sorgular:

```text
Gemlik Bursa + Kuaför / Berber
Gemlik Bursa + Güzellik Merkezi
Gemlik Bursa + Oto Servis
Nilüfer Bursa + Emlak Ofisi
```

## Testler

```powershell
pytest
```

Foundation smoke test:

```powershell
python -m web_lead_automation
```

## Lead Scoring v1

| Sinyal | Maksimum puan |
|---|---:|
| Google Places'ta website listelenmiyor | 40 |
| Telefon mevcut | 15 |
| Yorum hacmi | 20 |
| Rating | 15 |
| Hedef işletme türü | 10 |
| **Toplam** | **100** |

Amaç teorik olarak mükemmel skor değil, **hangi işletmenin önce aranması gerektiğini söyleyen pratik bir sıralama** üretmektir.

## CRM Durumları

```text
NEW
CONTACTED
INTERESTED
WON
LOST
```

Kalıcı CRM verisi mümkün olduğunca bizim ürettiğimiz satış bilgileriyle sınırlı tutulur. Google Places işletme detaylarının kalıcı kopyasını oluşturmak yerine Place ID, durum, not ve zaman bilgileri saklanır.

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
