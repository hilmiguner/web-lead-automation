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
Local preview kontrol et
        ↓
Paylaşılabilir HTTPS demo linki yayınla
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
| AI içerik | OpenAI Responses API |
| Demo paylaşımı | Netlify Deploy API |
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
- Hızlı score / telefon / CRM filtreleri
- Lead detay ekranı, CRM status ve not düzenleme
- Telefon, rating, yorum, adres ve Google Maps linki
- Açıklanabilir skor nedenleri
- Responsive, self-contained website demo template
- OpenAI Responses API ile strict JSON şemalı AI içerik taslağı
- Hero, hakkında, hizmet/bilgi kartları, CTA ve SEO metni üretimi
- Lead bazlı AI içeriğini dashboard üzerinden düzenleme
- Doğrulanmamış hizmet ve işletme iddialarını azaltan prompt kuralları
- Sektöre göre otomatik seçilen güvenli demo tema presetleri
- Kuaför/güzellik, otomotiv, emlak, lojistik, etkinlik, yapı ve genel kurumsal paletler
- Harici işletme fotoğrafı kopyalamadan CSS tabanlı güvenli placeholder görseller
- Kısa monogram / marka alanı desteği
- Dashboard üzerinden `Demo Oluştur / Yeniden Oluştur` akışı
- Lead başına deterministik ve dosya sistemi güvenli demo klasörü
- Her demo için self-contained `index.html` ve düzenlenebilir kaynak manifesti `demo.json`
- Aynı lead yeniden üretildiğinde aynı klasörün güncellenmesi
- Uygulama yeniden açıldığında son üretilen AI içerik/theme taslağının `demo.json` üzerinden geri yüklenebilmesi
- Streamlit içinde tek tıkla local demo preview
- Netlify Deploy API üzerinden paylaşılabilir HTTPS demo linki
- Public demo URL'sini SQLite CRM'e bağlama
- Public deploy'da yalnızca `index.html` dosyalarını yayınlama; `demo.json` local kalır
- Demo hub için `robots.txt` ile arama motoru taramasını engelleme
- Lead bazlı local demo temizleme ve Netlify yapılandırılmışsa public kopyayı senkronize etme

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

`.env` içinde Google Places, AI içerik üretimi ve opsiyonel public demo paylaşımı için gerekli ayarları tanımla:

```env
APP_ENV=development
LOG_LEVEL=INFO

GOOGLE_PLACES_API_KEY=your_google_api_key_here
GOOGLE_PLACES_TIMEOUT_SECONDS=10
GOOGLE_PLACES_PAGE_SIZE=20

OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-5.6-luna
OPENAI_TIMEOUT_SECONDS=30

LEAD_DB_PATH=data/leads.sqlite3
DEMO_OUTPUT_PATH=data/demos

NETLIFY_AUTH_TOKEN=your_netlify_token_here
NETLIFY_SITE_ID=your_netlify_site_id_here
NETLIFY_TIMEOUT_SECONDS=30
```

OpenAI API kullanımı ChatGPT aboneliğinden ayrı bir API anahtarı ve API hesabı gerektirir. Model `OPENAI_MODEL` ile değiştirilebilir. Varsayılan `gpt-5.6-luna`, demo metni gibi yüksek hacimli ve maliyet duyarlı işler için seçilmiştir.

Gerçek API anahtarları ve secret değerler GitHub'a commit edilmemelidir.

Google Places API anahtarı oluşturulmadan önce budget alert, quota ve API-key restriction adımları için [Google Cloud / Places API Setup Checklist](docs/GOOGLE_CLOUD_SETUP.md) uygulanmalıdır.

Paylaşılabilir demo için Netlify kurulumu, Project ID/Site ID, access token ve public proje görünürlüğü adımları [Netlify Demo Sharing Setup](docs/NETLIFY_SETUP.md) dosyasında yer alır.

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
6. Bir lead seç ve CRM durumunu / notunu güncelle.
7. `AI İçerik Taslağı Üret` alanında yalnızca doğruladığın hizmetleri opsiyonel olarak gir.
8. Üretilen hero, hakkında, kart, CTA ve SEO metinlerini kontrol edip düzenle.
9. Güvenli tema presetini ve istersen kısa marka işaretini seç.
10. `Demo Oluştur / Yeniden Oluştur` butonuna bas.
11. `Local Preview Aç / Kapat` ile demoyu Streamlit içinde kontrol et.
12. Netlify ayarları yapılmışsa `Paylaşılabilir Demo Yayınla` ile HTTPS link üret.
13. Üretilen public link otomatik olarak lead'in CRM kaydına bağlanır.

Her lead için local olarak `demo.json` oluşturulur. Bu dosya insan tarafından kontrol edilmiş içerik, theme seçimi ve demo üretim girdilerini saklar; aynı lead daha sonra tekrar açıldığında taslak geri yüklenebilir. `demo.json` Netlify deploy paketine dahil edilmez.

Demo dosya yapısı:

```text
data/demos/<lead-slug>/
├── index.html
└── demo.json
```

Netlify paylaşım yapısı:

```text
https://<demo-site>.netlify.app/<lead-slug>/
```

`Demo Dosyalarını Temizle` seçili lead'in local demo klasörünü kaldırır. Netlify yapılandırılmış ve lead daha önce yayınlanmışsa demo hub tekrar deploy edilerek public kopya da kaldırılır; başarılı remote senkronizasyondan sonra CRM `demo_url` alanı temizlenir.

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

AI ve Netlify provider testleri gerçek ücretli servis çağrıları yapmaz; `httpx.MockTransport` ile request/response sözleşmeleri doğrulanır. Gerçek Google Places, OpenAI ve Netlify uçtan uca kontrolü MVP saha doğrulamasında kullanıcı API hesaplarıyla yapılmalıdır.

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

Kalıcı CRM verisi mümkün olduğunca bizim ürettiğimiz satış bilgileriyle sınırlı tutulur. Google Places işletme detaylarının kalıcı kopyasını oluşturmak yerine Place ID, durum, not, demo URL ve zaman bilgileri saklanır.

Mevcut M2.x veritabanları uygulama açıldığında `demo_url` kolonu için geriye uyumlu şekilde migrate edilir; mevcut status ve not kayıtları korunur.

## AI Demo Website Yaklaşımı

MVP'de AI'ın her lead için sıfırdan serbest biçimde uygulama kodu yazması hedeflenmez. Daha hızlı ve güvenilir yöntem kullanılır:

```text
Lead verisi
   ↓
Yalnızca doğrulanmış işletme gerçekleri
   ↓
Structured AI içerik taslağı
   ↓
İnsan kontrolü / düzenleme
   ↓
Sektöre göre trusted theme preset
   ↓
Test edilmiş landing page template
   ↓
Lead'e özel index.html + demo.json
   ↓
Local preview
   ↓
Paylaşılabilir HTTPS demo linki
```

AI içerik katmanı işletmenin sahip olmadığı hizmetleri, ödülleri, faaliyet süresini, müşteri sayılarını, referansları, fiyatları veya garantileri gerçekmiş gibi üretmemesi için sınırlandırılmıştır. Doğrulanmış hizmet girilmezse hizmet kartları tarafsız bilgi ve iletişim metinlerine dönmelidir.

Tema katmanında model veya kullanıcıdan keyfi CSS kabul edilmez. Yalnızca uygulama içinde tanımlanmış presetler kullanılabilir. MVP görselleri harici işletme fotoğraflarını kalıcı olarak kopyalamak yerine CSS tabanlı soyut placeholder alanları kullanır.

Demo klasör adı işletme adından okunabilir bir slug ve Place ID'nin tek yönlü kısa hash'i ile oluşturulur. Tam Place ID klasör adına yazılmaz. Aynı lead için yeniden üretim yeni kopya oluşturmak yerine mevcut demo klasörünü günceller.

İlk hedef, bir lead için **5 dakikanın altında insan müdahalesiyle** satışta kullanılabilecek demo hazırlamaktır.

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
