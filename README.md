
# Telegram Trade Notify (Webhook → Telegram Channel)

Kiriman alert (TradingView / MT5 / sistem Anda) → webhook → dikirim ke channel Telegram (mis. **@GOLDENPIPSID**). Simple, cepat, dan tanpa platform pihak ketiga yang ribet.

## 1) Siapkan Bot & Channel
1. Buka **@BotFather**, buat bot. Simpan **BOT TOKEN**.
2. Tambahkan bot ke channel Anda (mis. **@GOLDENPIPSID**) sebagai **Admin** (izin: Post Messages).
3. Catat **CHAT_ID**: Anda bisa pakai `@GOLDENPIPSID` langsung, atau ID numerik `-100...`.

## 2) Deploy Webhook (Flask)
Deploy `app.py` di Render/Railway/Cloud Run/VPS Anda.
- Env vars:
  - `TELEGRAM_BOT_TOKEN` = token dari BotFather
  - `TELEGRAM_CHAT_ID`   = @channelusername (atau -100...)
  - `WEBHOOK_SECRET`     = rahasia bersama (contoh: `abc123`)
- Endpoint: `POST https://<domain-anda>/webhook`

### Coba Lokal
```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN=YOUR_TOKEN
export TELEGRAM_CHAT_ID=@GOLDENPIPSID
export WEBHOOK_SECRET=CHANGE_ME
python app.py
```
Lalu kirim contoh payload:
```bash
curl -X POST http://localhost:8000/webhook   -H "Content-Type: application/json"   -d @sample_alert.json
```

## 3) TradingView Alert
Di kotak **Message** pakai JSON seperti ini (ubah nilainya):
```json
{
  "secret": "CHANGE_ME",
  "symbol": "{{ticker}}",
  "side": "SELL",
  "price": "{{close}}",
  "time": "{{time}}",
  "entry": "{{close}}",
  "sl": "{{close}}",
  "tp1": "{{close}}",
  "tp2": "{{close}}",
  "rr": "1:2",
  "session": "NY",
  "fib_trigger": "85 (Break‑Reversal)",
  "bos": "Yes",
  "fvg": "Mitigated 50%",
  "ob": "H1 Bearish OB 3330–3340",
  "reason": "Checklist OK (#9)"
}
```
*Webhook URL* isi dengan alamat endpoint Anda.

## 4) MT5 / EA / Sistem Lain
Kirim `POST` JSON yang sama ke `/webhook`. Di MQL5 gunakan `WebRequest()` dengan header `Content-Type: application/json`.

## 5) Format Pesan
Pesan akan tampil rapi di Telegram (HTML). Anda bisa ubah `format_signal()` di `app.py` untuk gaya Anda sendiri.

## Keamanan & Good Practices
- Gunakan `WEBHOOK_SECRET` dan filter IP jika memungkinkan.
- Jangan spam: batasi frekuensi alert di sisi sumber.
- Monitoring: pantau log dan tambahkan retry/backoff bila perlu.
