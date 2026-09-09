# Google Cloud / Places API Setup Checklist

Bu dosya gerçek Google Places API anahtarı oluşturulurken uygulanacak maliyet ve güvenlik kontrollerini kalıcı olarak hatırlatır.

## Zorunlu kurulum kontrolleri

- [ ] Ayrı bir Google Cloud project oluştur.
- [ ] Billing hesabını projeye bağla.
- [ ] Yalnızca gereken Google Maps Platform / Places API (New) servislerini etkinleştir.
- [ ] API key oluştur ve key'i kaynak koda veya GitHub'a commit etme.
- [ ] API key'i yalnızca gereken Places API ile sınırla.
- [ ] Deployment ortamı netleştiğinde mümkün olan uygulama/IP kısıtlarını uygula.
- [ ] Cloud Billing altında budget oluştur.
- [ ] Düşük eşiklerde budget alert tanımla (ilk MVP için örneğin $5 ve $10 uyarıları).
- [ ] Google Maps Platform > Quotas ekranında Text Search (New) için düşük başlangıç kotası belirle.
- [ ] İlk saha testi boyunca quota ve billing ekranını düzenli kontrol et.

## Önemli: budget alert hard limit değildir

Google Cloud'un alerts-only budget özelliği harcamayı otomatik olarak durdurmaz; yalnızca belirlenen eşiklerde uyarı verir. Hesap/proje için destekleniyorsa spend-cap budget kullanılabilir. Aksi halde beklenmeyen maliyeti sınırlamak için budget alert ile birlikte API quota kullan.

## MVP için önerilen koruma yaklaşımı

1. Budget alert: düşük eşikler ($5 / $10 gibi).
2. Text Search (New): saha testi için düşük requests-per-minute kotasıyla başla (örneğin 10 request/minute) ve yalnızca gerçek ihtiyaç oluşursa yükselt.
3. API key restriction: key yalnızca gerekli Places API servislerini çağırabilsin.
4. Uygulama tarafı: filtre değişiklikleri ve UI rerun'ları yeni Places isteği üretmemeli; yalnızca kullanıcı açıkça `Lead Ara` dediğinde arama yapılmalı.
5. Ölçekleme öncesi gerçek günlük request sayısını ölç ve kotayı buna göre yeniden belirle.

Google Places API kotaları yöntem/proje bazında uygulanabilir. Quota aşıldığında ilgili servis istekleri durur; bu yüzden düşük kota hem maliyet koruması sağlar hem de runaway loop hatalarının etkisini sınırlar.

## Canlıya geçmeden önce

- [ ] Budget alert e-postasının doğru hesaba geldiğini doğrula.
- [ ] Quota değerini ekrandan tekrar kontrol et.
- [ ] `.env` içindeki `GOOGLE_PLACES_API_KEY` değerinin Git tarafından izlenmediğini doğrula.
- [ ] Bir adet gerçek Text Search testi yap.
- [ ] Google Cloud billing/usage ekranında çağrının göründüğünü doğrula.
- [ ] Beklenen field mask dışında gereksiz alan çekilmediğini kontrol et.

Bu kontroller tamamlanmadan geniş bölge/sektör taraması veya otomatik günlük tarama açılmamalıdır.
