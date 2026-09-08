# Web Lead Automation

Yerel işletmeler arasından **web sitesi olmayan veya dijital varlığı zayıf potansiyel müşterileri bulmak**, önceliklendirmek ve satış sürecini takip etmek için geliştirilen yarı otomatik lead-generation aracı.

Bu projenin ilk hedefi kusursuz bir SaaS geliştirmek değil; **olabildiğince hızlı şekilde gerçek müşteri adayları bulup web sitesi satmaya başlamaktır.**

## Hedef

İlk MVP aşağıdaki akışı mümkün olduğunca kısa sürede çalışır hale getirecek:

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
WhatsApp / arama için satış metni hazırla
        ↓
İletişime geç ve sonucu takip et
```

Örnek kullanım:

- Bölge: `Gemlik, Bursa`
- Sektör: `Kuaför`
- Sonuç: Web sitesi bulunmayan ve iletişim bilgisi olan işletmeler
- Öncelik: Yorum sayısı, puan, telefon bilgisi ve dijital görünürlüğe göre lead score

## MVP Kapsamı

MVP tamamlandığında kullanıcı şunları yapabilmeli:

- Bölge ve sektör girerek işletme arayabilmeli.
- Web sitesi bulunan / bulunmayan işletmeleri ayırabilmeli.
- Potansiyel müşterileri otomatik puanlayabilmeli.
- En değerli lead'leri sıralayabilmeli.
- Lead durumunu takip edebilmeli.
- Lead'e özel kısa satış mesajı oluşturabilmeli.
- Daha önce işlenen işletmelerin tekrar tekrar karşısına çıkmasını engelleyebilmeli.

### İlk CRM durumları

```text
NEW
CONTACTED
INTERESTED
WON
LOST
```

## MVP Dışında Tutulanlar

İlk satışları geciktirecek aşağıdaki özellikler MVP sonrasına bırakılacaktır:

- Tam kapsamlı SaaS mimarisi
- Kullanıcı üyelik sistemi
- Çoklu organizasyon / tenant desteği
- Ödeme altyapısı
- Karmaşık rol ve yetki sistemi
- Tam otonom WhatsApp / e-posta gönderimi
- Gelişmiş AI agent orkestrasyonu
- MCP entegrasyonlarının tamamı
- Otomatik production site deployment sistemi
- Mobil uygulama

Öncelik: **önce lead bulmak ve satış yapmak.**

## Planlanan MVP Teknolojileri

| Katman | Teknoloji |
|---|---|
| Dil | Python 3.12+ |
| Arayüz | Streamlit |
| Veri | SQLite |
| İşletme keşfi | Google Places API (New) |
| HTTP | httpx |
| Konfigürasyon | python-dotenv / pydantic-settings |
| Test | pytest |

Bu teknoloji seti, local bilgisayarda hızlı geliştirilebilen ve hızlı kullanılmaya başlanabilen bir MVP için seçilmiştir. Ürün doğrulandıktan sonra gerektiğinde ayrı API, PostgreSQL ve web frontend mimarisine geçilebilir.

## Önerilen Proje Yapısı

```text
web-lead-automation/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── repositories/
│   ├── services/
│   │   ├── places.py
│   │   ├── scoring.py
│   │   └── outreach.py
│   └── ui/
├── tests/
├── .env.example
├── .gitignore
├── pyproject.toml
├── README.md
└── ROADMAP.md
```

## Lead Scoring

İlk sürümde basit ve açıklanabilir bir puanlama kullanılacaktır.

Örnek sinyaller:

- Web sitesi bulunmuyor
- Telefon numarası mevcut
- Yüksek Google yorum sayısı
- İyi Google puanı
- İşletme aktif görünüyor
- Seçilen sektör satış açısından değerli
- Daha önce iletişime geçilmemiş

Puanlama ileride gerçek satış sonuçlarına göre güncellenecektir. Amaç teorik olarak mükemmel skor değil, **hangi işletmenin önce aranması gerektiğini söyleyen pratik bir sıralama** üretmektir.

## Veri Kullanımı

Google Places gibi harici veri kaynaklarının kullanım ve saklama koşulları dikkate alınacaktır. Kalıcı CRM verisi mümkün olduğunca bizim ürettiğimiz satış bilgileriyle sınırlı tutulacaktır:

- Harici işletme kimliği
- Lead durumu
- Kullanıcı notları
- İletişim geçmişi
- Lead score ve bizim ürettiğimiz metadata

API anahtarları veya diğer secret değerler GitHub reposuna commit edilmemelidir.

## Hızlı Başlangıç

Proje kodu oluşturulduktan sonra hedef kullanım şekli:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
streamlit run app/main.py
```

`.env` örneği:

```env
GOOGLE_PLACES_API_KEY=your_api_key_here
DATABASE_PATH=data/leads.db
```

> Not: Bu komutlar MVP implementasyonu ilerledikçe doğrulanıp güncellenecektir.

## İlk Satış Modeli

Başlangıç hedefi, web sitesi olmayan küçük işletmelere hızlı hazırlanabilen bir web sitesi paketi sunmaktır.

Örnek başlangıç teklifi:

- Tek sayfalık modern web sitesi
- Mobil uyumlu tasarım
- WhatsApp iletişim butonu
- Google Maps
- Hizmetler / işletme bilgileri
- Temel SEO
- Yayına alma

Başlangıç satış fiyatı yaklaşık **4.990–5.000 TL** olarak test edilebilir. Gerçek satışlardan sonra fiyat ve paketler yeniden değerlendirilecektir.

## Başarı Kriteri

MVP'nin başarı kriteri kod miktarı değildir.

İlk hedefler:

1. Uygulama gerçek işletmeleri bulabiliyor.
2. Web sitesi olmayan lead'leri ayıklayabiliyor.
3. Kullanıcı her gün aranabilecek kaliteli bir lead listesi çıkarabiliyor.
4. Lead'lerin durumu takip edilebiliyor.
5. Sistem kullanılarak ilk ücretli müşteri kazanılabiliyor.

İlk müşteri kazanılmadan önce gereksiz platform özellikleri geliştirilmemelidir.

## Roadmap

Geliştirme sırası ve MVP sınırı için [ROADMAP.md](ROADMAP.md) dosyasına bakın.
