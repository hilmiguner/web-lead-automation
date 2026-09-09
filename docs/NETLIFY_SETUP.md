# Netlify Demo Sharing Setup

M4.5 paylaşım akışı, local olarak oluşturulan statik demo sayfalarını tek bir Netlify projesine ZIP deploy olarak yükler.

## Neden tek site?

Her lead için ayrı Netlify projesi açmak yerine tüm demolar aynı site altında ayrı slug'larla yayınlanır:

```text
https://<site>.netlify.app/<lead-slug>/
```

Bu yaklaşım MVP'de kurulum ve operasyon maliyetini düşük tutar.

## 1. Netlify hesabı ve proje oluştur

1. Netlify hesabına giriş yap.
2. Demo yayınları için ayrı bir proje/site oluştur.
3. Projenin müşteriye gönderilecek linkler için **public** erişilebilir olduğunu doğrula.
4. Project configuration içinden **Project ID / Site ID** değerini al.

> Not: Yeni Netlify takımlarında proje görünürlüğü private varsayılanına sahip olabilir. Demo paylaşmadan önce siteyi anonim kullanıcıların açabildiğini kontrol et.

## 2. Personal Access Token oluştur

Netlify kullanıcı ayarlarında:

```text
Applications
→ Personal access tokens
→ New access token
```

Token'a açıklayıcı bir isim ve mümkünse uygun bir expiration date ver.

Token bir parola gibi korunmalıdır. GitHub'a veya uygulama kaynak koduna commit edilmemelidir.

## 3. `.env` ayarlarını yap

```env
NETLIFY_AUTH_TOKEN=your_personal_access_token
NETLIFY_SITE_ID=your_project_id
NETLIFY_TIMEOUT_SECONDS=30
```

`.env` zaten `.gitignore` kapsamındadır.

## 4. Dashboard akışı

```text
Lead seç
→ AI içeriğini üret / kontrol et
→ Demo Oluştur
→ Local Preview Aç
→ Paylaşılabilir Demo Yayınla
```

Yayınlama işlemi:

1. `data/demos` altındaki mevcut demo `index.html` dosyalarını toplar.
2. Local `demo.json` manifestlerini **yayınlamaz**.
3. Arama motorları için `robots.txt` ile `Disallow: /` ekler.
4. Netlify Deploy API'ye ZIP olarak production deploy yapar.
5. Deploy `ready` olana kadar durumunu kontrol eder.
6. Seçilen lead için oluşan HTTPS demo linkini SQLite CRM'e kaydeder.

## 5. Demo temizleme

Dashboard'daki `Demo Dosyalarını Temizle` aksiyonu seçili lead'in local demo klasörünü kaldırır.

Netlify ayarları mevcutsa sistem ardından demo hub'ı tekrar deploy ederek public kopyayı da senkronize eder ve lead'in CRM `demo_url` alanını temizler.

Netlify ayarları yoksa local dosya silinir fakat daha önce yayınlanmış public URL otomatik kaldırılamaz; bu durumda CRM linki bilerek korunur.

## Güvenlik notları

- `NETLIFY_AUTH_TOKEN` hiçbir zaman repo içine yazılmamalıdır.
- `demo.json` public deploy'a dahil edilmez.
- Public demo site yalnızca satış önizlemesi amacıyla kullanılmalıdır.
- Demo template üzerinde `Demo Önizleme` işareti ve resmi site olmadığını belirten açıklama korunur.
- Gereksiz deploy döngülerinden kaçınılmalıdır; her `Paylaşılabilir Demo Yayınla` işlemi gerçek bir Netlify deploy oluşturur.
