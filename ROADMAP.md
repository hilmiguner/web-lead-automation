# Web Lead Automation — Roadmap

Bu roadmap'in amacı **olabildiğince kısa sürede kullanılabilir bir MVP çıkarıp gerçek müşteri aramaya başlamaktır**.

Ana prensip:

> Gelir üretmeyen veya ilk müşteriyi bulmayı geciktiren özellik MVP sonrasına bırakılır.

---

## MVP Tanımı

MVP tamamlandığında uygulama:

1. Kullanıcının seçtiği bölge ve sektörde işletmeleri bulacak.
2. Web sitesi olmayan işletmeleri ayıklayacak.
3. Lead'leri puanlayıp sıralayacak.
4. Lead durumlarını local CRM'de tutacak.
5. Seçilen bir lead için AI destekli kişiselleştirilmiş demo web sitesi üretecek.
6. Demo siteyi kullanıcıya önizletecek ve paylaşılabilir hale getirecek.
7. Lead'e özel kısa satış mesajı hazırlayacak.
8. Kullanıcının günlük olarak müşteri aramaya başlayabileceği basit bir arayüz sunacak.

Bunlar çalıştığında **MVP geliştirmesi durdurulacak ve ürün gerçek hayatta test edilmeye başlanacak.**

---

# Phase 0 — Foundation

## M0.1 — Proje iskeleti

- [x] Python proje yapısını oluştur
- [x] `pyproject.toml`
- [x] `.gitignore`
- [x] `.env.example`
- [x] Temel config yönetimi
- [x] Logging altyapısı
- [x] Test altyapısı

**Çıkış kriteri:**

Proje temiz ortamda kurulabiliyor ve test komutu çalışıyor.

---

# Phase 1 — Lead Finder

## M1.1 — Google Places istemcisi

- [x] Google Places API (New) entegrasyonu
- [x] Text Search desteği
- [x] Bölge + sektör sorgusu
- [x] Gerekli minimum field'ları çek
- [x] Timeout ve temel hata yönetimi
- [x] API anahtarını environment üzerinden al

Örnek sorgular:

```text
kuaför Gemlik Bursa
oto servis Gemlik Bursa
güzellik merkezi Bursa
emlak ofisi Nilüfer Bursa
```

## M1.2 — Website filtresi

- [x] Website bilgisi bulunan işletmeleri tespit et
- [x] Website bulunmayan işletmeleri ayrı listele
- [x] Eksik / belirsiz website durumunu güvenli şekilde işle

## M1.3 — Lead scoring v1

- [x] 0–100 arası skor
- [x] Website yokluğu
- [x] Telefon varlığı
- [x] Yorum sayısı
- [x] Rating
- [x] İşletme türü
- [x] Skor nedenlerini kullanıcıya göster

**Çıkış kriteri:**

Terminal/test katmanından gerçek bir bölge + sektör sorgusu yapıldığında, web sitesi olmayan işletmeler skorlanmış şekilde dönebiliyor.

---

# Phase 2 — Minimal CRM

## M2.1 — SQLite veri katmanı

- [x] SQLite database oluştur
- [x] Lead kaydı
- [x] Harici işletme kimliği ile duplicate kontrolü
- [x] Lead status
- [x] Kullanıcı notu
- [x] Created / updated timestamp

İlk durumlar:

```text
NEW
CONTACTED
INTERESTED
WON
LOST
```

## M2.2 — Lead geçmişi

- [x] Daha önce görülen işletmeyi işaretle
- [x] Daha önce iletişime geçilen lead'i göster
- [x] WON / LOST lead'leri yeni arama sonuçlarından ayırt et

**Çıkış kriteri:**

Uygulama kapatılıp yeniden açıldığında satış pipeline bilgileri kaybolmuyor.

---

# Phase 3 — Kullanılabilir Dashboard

## M3.1 — Streamlit arayüz

- [x] Bölge input'u
- [x] Sektör input'u / preset seçenekleri
- [x] `Lead Ara` butonu
- [x] Sonuç tablosu
- [x] Lead score sıralaması
- [x] Website durumu
- [x] Telefon varlığı
- [x] Rating / yorum bilgisi

## M3.2 — Lead detay ekranı

- [ ] Lead detaylarını göster
- [ ] Score açıklaması
- [ ] CRM status değiştir
- [ ] Not ekle
- [ ] Google Maps / işletme kaynağına gitmek için bağlantı

## M3.3 — Hızlı filtreler

- [ ] Sadece website olmayanlar
- [ ] Minimum skor
- [ ] Sadece telefon numarası olanlar
- [ ] CRM status filtresi

**Çıkış kriteri:**

Kullanıcı kod veya terminal kullanmadan uygulamayı açıp günlük lead listesi oluşturabiliyor.

---

# Phase 4 — AI Website Demo Creation Automation

Bu faz MVP'nin satış tarafındaki temel fark yaratıcı özelliğidir.

Amaç, seçilen yüksek potansiyelli bir lead için **dakikalar içinde müşteriye gösterilebilir kişiselleştirilmiş tek sayfalık demo web sitesi** üretmektir.

MVP'de AI'ın her müşteri için sıfırdan serbest biçimde uygulama kodu yazması hedeflenmez. Daha hızlı, ucuz ve güvenilir bir yaklaşım kullanılacak:

```text
Lead verisi
   ↓
AI içerik + marka önerisi
   ↓
Test edilmiş demo template
   ↓
Kişiselleştirilmiş statik site
   ↓
Preview / paylaşılabilir demo
```

## M4.1 — Demo template foundation

İlk MVP için **tek güçlü ve sektörler arası kullanılabilir landing page template** yeterlidir.

- [ ] Responsive tek sayfalık demo template
- [ ] Hero alanı
- [ ] Hizmetler
- [ ] Hakkında
- [ ] Güven / sosyal kanıt alanı
- [ ] İletişim
- [ ] WhatsApp CTA
- [ ] Telefon CTA
- [ ] Maps / adres alanı
- [ ] Mobil uyumluluk
- [ ] Demo olduğunu belirten uygun preview işareti

İlk satışlardan sonra gerekirse ayrı sektör template'leri eklenir:

- Kuaför / berber
- Güzellik merkezi
- Oto servis
- Klinik
- Emlak
- Genel kurumsal

## M4.2 — AI içerik üretimi

- [ ] LLM API entegrasyonu
- [ ] İşletme adı ve sektöründen hero başlığı üret
- [ ] Kısa işletme tanıtımı üret
- [ ] Hizmet başlıkları ve açıklamaları üret
- [ ] CTA metinleri üret
- [ ] SEO title / description taslağı üret
- [ ] Sektöre uygun ton belirle
- [ ] Halüsinasyonları azaltmak için bilinmeyen gerçekleri uydurmama kuralı
- [ ] Üretilen içeriği kullanıcıya düzenlet

AI yalnızca bilinen işletme verisini ve güvenli genel sektör bilgisini kullanmalı. İşletmenin sahip olmadığı hizmetler, ödüller, müşteri sayıları veya doğrulanmamış iddialar gerçekmiş gibi yazılmamalıdır.

## M4.3 — Görsel ve tema kişiselleştirme

- [ ] Sektöre göre tema / stil preset'i seç
- [ ] Renk paleti önerisi
- [ ] İşletme adı / logo alanı
- [ ] Demo için güvenli placeholder veya lisansı uygun görsel desteği
- [ ] İzinsiz işletme fotoğraflarını kalıcı olarak kopyalamama

MVP için özel AI görsel üretimi zorunlu değildir; satış dönüşümüne etkisi kanıtlanırsa daha sonra eklenir.

## M4.4 — Demo oluşturma pipeline'ı

Dashboard üzerinden:

```text
Lead seç
↓
Demo Oluştur
↓
AI içerikleri üret
↓
Template'i doldur
↓
Dosyaları oluştur
↓
Preview aç
```

- [ ] `Demo Oluştur` aksiyonu
- [ ] Lead başına ayrı demo slug / klasör
- [ ] Tekrar üretme desteği
- [ ] Kullanıcı düzenlemelerini koruyabilecek basit yapı
- [ ] Oluşturma hatalarını anlaşılır göster

## M4.5 — Preview ve paylaşım

- [ ] Local preview
- [ ] Tek tık / tek komutla preview oluşturma
- [ ] En az bir paylaşılabilir preview deployment yöntemi
- [ ] Demo linkini CRM kaydına bağla
- [ ] Eski / kaybedilmiş lead demolarını temizleme yolu

**Çıkış kriteri:**

Dashboard'da bir lead seçilip `Demo Oluştur` denildiğinde, işletme adı/sektörü/iletişim bilgileriyle kişiselleştirilmiş profesyonel tek sayfalık bir demo hazırlanıyor ve kullanıcı müşteriye gösterebileceği bir preview elde ediyor.

Hedef operasyon süresi:

> Bir lead için ilk demo hazırlama: **5 dakikanın altında insan müdahalesi**.

---

# Phase 5 — Outreach Assistant

Bu aşamada **otomatik spam gönderimi yapılmayacak**. Sistem kullanıcıya hızlı iletişim kurması için yardımcı olacak.

## M5.1 — Satış mesajı üretimi

- [ ] İşletme adına özel WhatsApp metni
- [ ] Hazırlanan demo linkini mesaja ekleme seçeneği
- [ ] Kısa telefon görüşmesi açılışı
- [ ] Alternatif mesaj şablonları
- [ ] Mesajı tek tıkla kopyalama

Örnek yaklaşım:

```text
Merhaba, işletmenizi internette incelerken mevcut bir web sitenize rastlamadım.
İşletmeniz için nasıl görünebileceğini göstermek amacıyla kısa bir demo hazırladım...
```

Mesajların yanıltıcı, saldırgan veya işletme adına içerik yayınlanmış izlenimi vermemesine dikkat edilecek.

## M5.2 — İletişim takibi

- [ ] `CONTACTED` durumuna hızlı geçiş
- [ ] Son iletişim tarihi
- [ ] Kısa görüşme notu
- [ ] Takip edilmesi gereken lead'leri göster

**Çıkış kriteri:**

Kullanıcı bir lead bulduktan sonra demo linki dahil kişiselleştirilmiş satış metnini birkaç saniye içinde alıp iletişime geçebiliyor.

---

# MVP STOP POINT

Aşağıdaki uçtan uca senaryo çalıştığında **yeni özellik geliştirmeyi geçici olarak durdur:**

```text
Uygulamayı aç
↓
Gemlik + Kuaför seç
↓
Lead Ara
↓
Web sitesi olmayan işletmeleri gör
↓
Score'a göre sırala
↓
Yüksek skorlu bir lead aç
↓
Demo Oluştur
↓
AI tarafından kişiselleştirilmiş demo siteyi kontrol et
↓
Paylaşılabilir demo linkini al
↓
Demo linkli satış mesajını kopyala
↓
İşletmeyle iletişime geç
↓
CRM durumunu CONTACTED yap
```

Bu noktadan sonra amaç:

- Her gün gerçek lead'ler bulmak
- En iyi lead'ler için hızlı demo üretmek
- İşletmeleri aramak / mesaj atmak
- Demo ile yapılan satışın dönüşüm oranını ölçmek
- Hangi sektörlerin daha iyi cevap verdiğini görmek
- İlk ücretli müşteriyi kazanmak

**İlk gerçek kullanım verisi gelmeden büyük mimari değişiklik yapılmamalıdır.**

---

# Phase 6 — Automation & MCP

Manuel / yarı otomatik sürecin gerçekten çalıştığı kanıtlandıktan sonra otomasyon artırılır.

## M6.1 — MCP server

Planlanan tool'lar:

```text
search_business_leads
get_business_lead
list_tracked_leads
update_lead_status
generate_website_demo
generate_outreach_message
```

## M6.2 — Günlük otomasyon

- [ ] Sektör / bölge tarama planları
- [ ] Duplicate engelleme
- [ ] Yeni yüksek skorlu lead raporu
- [ ] Günlük satış listesi
- [ ] Demo oluşturmaya uygun lead önerileri

## M6.3 — Demo automation v2

- [ ] Yüksek skorlu lead'ler için demo hazırlama kuyruğu
- [ ] Birden fazla sektör template'i
- [ ] AI görsel üretimi gerektiğinde entegrasyon
- [ ] Otomatik preview deployment
- [ ] Demo kalite kontrolleri

## M6.4 — Follow-up önerileri

- [ ] İletişimden sonra belirli süre geçen lead'leri bul
- [ ] Takip mesajı taslağı üret
- [ ] Kullanıcı onayı olmadan mesaj gönderme

---

# Phase 7 — Revenue Expansion

Gerçek müşteriler geldikten sonra değerlendirilecek.

- [ ] Bakım / hosting aboneliği takibi
- [ ] Domain yenileme hatırlatmaları
- [ ] Upsell fırsatları
- [ ] SEO paketi
- [ ] Google Business optimizasyonu
- [ ] Randevu sistemi
- [ ] Çoklu dil
- [ ] Aylık bakım paketleri

---

# MVP Sonrasına Bilerek Ertelenen Teknik Konular

Aşağıdakiler ihtiyaç ortaya çıkmadan geliştirilmemelidir:

- PostgreSQL migration
- FastAPI backend
- Next.js / React dashboard
- Docker / Kubernetes
- Gelişmiş cloud altyapısı
- User authentication
- RBAC
- Multi-tenancy
- Queue sistemi
- Redis
- Event-driven architecture
- Mikroservisler
- Gelişmiş observability
- Mobil uygulama
- Çoklu AI provider orchestration
- Tam otonom outreach

Bunlar kötü fikirler değildir; **ilk müşteriyi kazanmadan önce yanlış önceliktir.**
Not: MVP'deki paylaşılabilir demo için gereken minimum deployment çözümü bu ertelemenin dışındadır.

---

# Önerilen İlk Hedef Sektörler

İlk test için küçük bir sektör havuzu kullanılmalı:

1. Kuaför / berber
2. Güzellik merkezi
3. Oto servis
4. Emlak ofisi
5. Nakliyat firması
6. Düğün salonu / organizasyon
7. Yerel yapı / tadilat işletmeleri

Başlangıç bölgesi:

```text
Gemlik → Bursa → yakın ilçeler
```

Önce dar bölgede demo, satış mesajı ve teklif doğrulanacak; sonra ölçeklenecek.

---

# Takip Edilecek Basit Metrikler

İlk aşamada yalnızca gelirle ilişkili metrikler tutulmalı:

- Bulunan lead sayısı
- Website olmayan lead sayısı
- Demo oluşturulan lead sayısı
- İletişime geçilen lead sayısı
- Cevap veren lead sayısı
- Demo görüntüleme / geri dönüş sayısı (ölçülebiliyorsa)
- Görüşme sayısı
- Teklif sayısı
- WON sayısı
- Satış tutarı

Örnek funnel:

```text
100 lead
  ↓
40 uygun lead
  ↓
15 demo
  ↓
15 iletişim
  ↓
5 cevap
  ↓
2 görüşme
  ↓
1 satış
```

Gerçek oranlar ölçüldükçe lead scoring, demo yaklaşımı ve sektör seçimi buna göre güncellenecektir.

---

# Definition of Done — MVP

MVP ancak aşağıdakilerin tamamı sağlandığında bitmiş sayılır:

- [ ] Temiz kurulum başarılı
- [ ] Google Places gerçek sorgusu başarılı
- [ ] Website filtresi çalışıyor
- [ ] Lead scoring çalışıyor
- [ ] Duplicate kontrolü çalışıyor
- [ ] SQLite CRM çalışıyor
- [ ] Streamlit dashboard kullanılabilir
- [ ] Lead status ve notlar kalıcı
- [ ] AI ile lead'e özel demo içerikleri üretilebiliyor
- [ ] Demo template otomatik doldurulabiliyor
- [ ] Demo preview çalışıyor
- [ ] Paylaşılabilir demo linki üretilebiliyor
- [ ] Demo linkli outreach mesajı üretilebiliyor
- [ ] Temel testler yeşil
- [ ] README kurulum adımları doğrulanmış
- [ ] Gerçek bir günlük lead listesi üretildi
- [ ] En az bir gerçek lead için uçtan uca demo üretildi

Sonrasında geliştirme durdurulur ve saha testi başlar.