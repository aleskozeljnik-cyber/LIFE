from .db import get_connection

async def generate_today_summary(user_id: str) -> str:
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("select title,due_at,amount,currency,priority from obligations where user_id=%s and status='open' and (due_at is null or due_at::date=current_date) order by case priority when 'high' then 1 when 'medium' then 2 else 3 end,due_at nulls last", (user_id,))
            rows = await cur.fetchall()
            if not rows:
                content = "Nothing due today. LIFE will keep watching connected sources."
            else:
                parts = []
                for row in rows[:8]:
                    amount = f" — {row['amount']} {row['currency']}" if row['amount'] is not None else ""
                    due = f" by {row['due_at'].strftime('%H:%M')}" if row['due_at'] and hasattr(row['due_at'], 'strftime') else ""
                    parts.append(f"{row['title']}{due}{amount}")
                content = "Today: " + "; ".join(parts)
            await cur.execute("insert into daily_summaries (user_id,summary_date,content) values (%s,current_date,%s) on conflict (user_id,summary_date) do update set content=excluded.content", (user_id,content))
        await conn.commit()
    return content