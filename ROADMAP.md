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
5. Lead'e özel kısa satış mesajı hazırlayacak.
6. Kullanıcının günlük olarak müşteri aramaya başlayabileceği basit bir arayüz sunacak.

Bunlar çalıştığında **MVP geliştirmesi durdurulacak ve ürün gerçek hayatta test edilmeye başlanacak.**

---

# Phase 0 — Foundation

## M0.1 — Proje iskeleti

- [ ] Python proje yapısını oluştur
- [ ] `pyproject.toml`
- [ ] `.gitignore`
- [ ] `.env.example`
- [ ] Temel config yönetimi
- [ ] Logging altyapısı
- [ ] Test altyapısı

**Çıkış kriteri:**

Proje temiz ortamda kurulabiliyor ve test komutu çalışıyor.

---

# Phase 1 — Lead Finder

## M1.1 — Google Places istemcisi

- [ ] Google Places API (New) entegrasyonu
- [ ] Text Search desteği
- [ ] Bölge + sektör sorgusu
- [ ] Gerekli minimum field'ları çek
- [ ] Timeout ve temel hata yönetimi
- [ ] API anahtarını environment üzerinden al

Örnek sorgular:

```text
kuaför Gemlik Bursa
oto servis Gemlik Bursa
güzellik merkezi Bursa
emlak ofisi Nilüfer Bursa
```

## M1.2 — Website filtresi

- [ ] Website bilgisi bulunan işletmeleri tespit et
- [ ] Website bulunmayan işletmeleri ayrı listele
- [ ] Eksik / belirsiz website durumunu güvenli şekilde işle

## M1.3 — Lead scoring v1

- [ ] 0–100 arası skor
- [ ] Website yokluğu
- [ ] Telefon varlığı
- [ ] Yorum sayısı
- [ ] Rating
- [ ] İşletme türü
- [ ] Skor nedenlerini kullanıcıya göster

**Çıkış kriteri:**

Terminal/test katmanından gerçek bir bölge + sektör sorgusu yapıldığında, web sitesi olmayan işletmeler skorlanmış şekilde dönebiliyor.

---

# Phase 2 — Minimal CRM

## M2.1 — SQLite veri katmanı

- [ ] SQLite database oluştur
- [ ] Lead kaydı
- [ ] Harici işletme kimliği ile duplicate kontrolü
- [ ] Lead status
- [ ] Kullanıcı notu
- [ ] Created / updated timestamp

İlk durumlar:

```text
NEW
CONTACTED
INTERESTED
WON
LOST
```

## M2.2 — Lead geçmişi

- [ ] Daha önce görülen işletmeyi işaretle
- [ ] Daha önce iletişime geçilen lead'i göster
- [ ] WON / LOST lead'leri yeni arama sonuçlarından ayırt et

**Çıkış kriteri:**

Uygulama kapatılıp yeniden açıldığında satış pipeline bilgileri kaybolmuyor.

---

# Phase 3 — Kullanılabilir Dashboard

## M3.1 — Streamlit arayüz

- [ ] Bölge input'u
- [ ] Sektör input'u / preset seçenekleri
- [ ] `Lead Ara` butonu
- [ ] Sonuç tablosu
- [ ] Lead score sıralaması
- [ ] Website durumu
- [ ] Telefon varlığı
- [ ] Rating / yorum bilgisi

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

# Phase 4 — Outreach Assistant

Bu aşamada **otomatik spam gönderimi yapılmayacak**. Sistem kullanıcıya hızlı iletişim kurması için yardımcı olacak.

## M4.1 — Satış mesajı üretimi

- [ ] İşletme adına özel WhatsApp metni
- [ ] Kısa telefon görüşmesi açılışı
- [ ] Alternatif mesaj şablonları
- [ ] Mesajı tek tıkla kopyalama

Örnek yaklaşım:

```text
Merhaba, işletmenizi internette incelerken mevcut bir web sitenize rastlamadım.
Küçük işletmeler için uygun fiyatlı, mobil uyumlu web siteleri hazırlıyorum...
```

Mesajların yanıltıcı, saldırgan veya işletme adına içerik yayınlanmış izlenimi vermemesine dikkat edilecek.

## M4.2 — İletişim takibi

- [ ] `CONTACTED` durumuna hızlı geçiş
- [ ] Son iletişim tarihi
- [ ] Kısa görüşme notu
- [ ] Takip edilmesi gereken lead'leri göster

**Çıkış kriteri:**

Kullanıcı bir lead bulduktan sonra birkaç saniye içinde kişiselleştirilmiş satış metni alıp iletişime geçebiliyor.

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
Bir lead aç
↓
Satış mesajını kopyala
↓
İşletmeyle iletişime geç
↓
CRM durumunu CONTACTED yap
```

Bu noktadan sonra amaç:

- Her gün gerçek lead'ler bulmak
- İşletmeleri aramak / mesaj atmak
- Hangi sektörlerin daha iyi cevap verdiğini görmek
- İlk ücretli müşteriyi kazanmak

**İlk gerçek kullanım verisi gelmeden büyük mimari değişiklik yapılmamalıdır.**

---

# Phase 5 — İlk Satış Sonrası Demo Generator

MVP gerçek kullanımda doğrulandıktan sonra.

## M5.1 — Site template sistemi

İlk template adayları:

- [ ] Kuaför / berber
- [ ] Güzellik merkezi
- [ ] Oto servis
- [ ] Klinik
- [ ] Emlak
- [ ] Genel kurumsal

## M5.2 — Demo veri üretimi

- [ ] İşletme adına göre başlıklar
- [ ] Hizmet metinleri
- [ ] CTA'lar
- [ ] İletişim bölümü
- [ ] Maps / WhatsApp entegrasyonu

## M5.3 — Preview

- [ ] Local preview
- [ ] Tek komutla demo üretimi
- [ ] Gerekiyorsa geçici preview deployment

Amaç: bir lead için satış öncesi demo hazırlama süresini dakikalar seviyesine indirmek.

---

# Phase 6 — Automation & MCP

Manuel sürecin gerçekten çalıştığı kanıtlandıktan sonra otomasyon artırılır.

## M6.1 — MCP server

Planlanan tool'lar:

```text
search_business_leads
get_business_lead
list_tracked_leads
update_lead_status
generate_outreach_message
```

## M6.2 — Günlük otomasyon

- [ ] Sektör / bölge tarama planları
- [ ] Duplicate engelleme
- [ ] Yeni yüksek skorlu lead raporu
- [ ] Günlük satış listesi

## M6.3 — Follow-up önerileri

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
- Next.js / React frontend
- Docker / Kubernetes
- Cloud deployment altyapısı
- User authentication
- RBAC
- Multi-tenancy
- Queue sistemi
- Redis
- Event-driven architecture
- Mikroservisler
- Gelişmiş observability
- Mobil uygulama

Bunlar kötü fikirler değildir; **ilk müşteriyi kazanmadan önce yanlış önceliktir.**

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

Önce dar bölgede satış mesajı ve teklif doğrulanacak; sonra ölçeklenecek.

---

# Takip Edilecek Basit Metrikler

İlk aşamada yalnızca gelirle ilişkili metrikler tutulmalı:

- Bulunan lead sayısı
- Website olmayan lead sayısı
- İletişime geçilen lead sayısı
- Cevap veren lead sayısı
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
30 iletişim
  ↓
8 cevap
  ↓
3 görüşme
  ↓
1 satış
```

Gerçek oranlar ölçüldükçe lead scoring ve sektör seçimi buna göre güncellenecektir.

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
- [ ] Outreach mesajı üretilebiliyor
- [ ] Temel testler yeşil
- [ ] README kurulum adımları doğrulanmış
- [ ] Gerçek bir günlük lead listesi üretildi

Sonrasında geliştirme durdurulur ve saha testi başlar.
