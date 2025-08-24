const esc = (x) =>
  x == null ? "-" : String(x).replace(/[&<>"']/g, (m) => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[m]));

export async function onRequestPost({ request, env }) {
  if (!request.headers.get("content-type")?.includes("application/json"))
    return new Response("Expecting JSON", { status: 400 });

  let data;
  try { data = await request.json(); } catch { return new Response("Bad JSON", { status: 400 }); }

  if (String(data.secret || "") !== String(env.WEBHOOK_SECRET || ""))
    return new Response("Unauthorized", { status: 401 });

  const symbol = esc(data.symbol ?? data.ticker ?? data.pair);
  const side   = esc(data.side ?? data.direction ?? "?");
  const price  = esc(data.price ?? data.entry ?? data.close);
  const sl     = esc(data.sl ?? data.stop ?? data.stop_loss);
  const tp1    = esc(data.tp1 ?? data.tp_1);
  const tp2    = esc(data.tp2 ?? data.tp_2);
  const rr     = esc(data.rr ?? data.risk_reward);
  const sess   = esc(data.session ?? data.sess);
  const fib    = esc(data.fib_trigger ?? data.fib);
  const bos    = esc(data.bos ?? data.break_of_structure);
  const fvg    = esc(data.fvg);
  const ob     = esc(data.ob ?? data.order_block);
  const reason = esc(data.reason ?? data.notes ?? data.setup);

  let timeStr = "-";
  const tm = data.time ?? data.timestamp;
  try {
    if (typeof tm === "number") {
      const ms = tm > 1e12 ? tm : tm * 1000;
      timeStr = new Date(ms).toISOString().replace("T"," ").replace("Z"," UTC");
    } else if (typeof tm === "string") timeStr = esc(tm);
  } catch {}

  const lines = [];
  lines.push(`🟢 <b>TRADING ALERT</b>`);
  lines.push(`• <b>Symbol</b>: ${symbol}`);
  lines.push(`• <b>Side</b>: ${side}  @ <b>${price}</b>`);
  lines.push(`• <b>Time</b>: ${timeStr}`);
  if (sl !== "-" || tp1 !== "-" || tp2 !== "-") lines.push(`• <b>SL</b>: ${sl}  |  <b>TP1</b>: ${tp1}  |  <b>TP2</b>: ${tp2}`);
  const extras = [];
  if (rr !== "-")   extras.push(`RR ${rr}`);
  if (sess !== "-") extras.push(`Session ${sess}`);
  if (fib !== "-")  extras.push(`Fibo ${fib}`);
  if (bos !== "-")  extras.push(`BOS ${bos}`);
  if (fvg !== "-")  extras.push(`FVG ${fvg}`);
  if (ob !== "-")   extras.push(`OB ${ob}`);
  if (extras.length) lines.push("• " + extras.join(" · "));
  if (reason !== "-") lines.push(`• <b>Notes</b>: ${reason}`);

  const resp = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      chat_id: env.TELEGRAM_CHAT_ID,
      text: lines.join("\\n"),
      parse_mode: "HTML",
      disable_web_page_preview: true,
    }),
  });

  if (!resp.ok) return new Response(`Telegram error: ${await resp.text()}`, { status: 502 });
  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}
