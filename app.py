
@app.post("/api/answer")
def api_answer():
    j = request.get_json(silent=True) or {}
    a = get_attempt(j.get("token", ""))

    qi, ch = j.get("q"), j.get("choice")

    if not a or a["finished"] is not None:
        return err("bad")

    if not (
        isinstance(qi, int) and not isinstance(qi, bool)
        and isinstance(ch, int) and not isinstance(ch, bool)
        and 0 <= qi < TOTAL and 0 <= ch < 4
    ):
        return err("bad")

    d = db()
    q = QUESTIONS[qi]
    lg = a["lang"] or "uz"

    cur = d.execute(
        """INSERT OR IGNORE INTO answers
        (attempt_id, qi, choice, qtext, chosen,
         correct_text, is_correct, ts)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            a["id"], qi, ch,
            q[lg]["q"],
            q[lg]["o"][ch],
            q[lg]["o"][q["a"]],
            int(ch == q["a"]),
            int(time.time())
        )
    )

    d.commit()

    # To'g'ri javob foydalanuvchiga yuborilmaydi.
    return jsonify(
        saved=True,
        already=(cur.rowcount == 0)
    )


@app.post("/api/finish")
def api_finish():
    j = request.get_json(silent=True) or {}
    a = get_attempt(j.get("token", ""))

    if not a:
        return err("bad")

    d = db()

    if a["finished"] is None:
        answered = d.execute(
            "SELECT COUNT(*) FROM answers WHERE attempt_id=?",
            (a["id"],)
        ).fetchone()[0]

        # Barcha savollar javoblanmaguncha test tugamaydi.
        if answered < TOTAL:
            return jsonify(
                error="incomplete",
                answered=answered,
                total=TOTAL
            ), 400

        score = d.execute(
            """SELECT COALESCE(SUM(is_correct), 0)
            FROM answers WHERE attempt_id=?""",
            (a["id"],)
        ).fetchone()[0]

        d.execute(
            """UPDATE attempts
            SET finished=?, score=?, total=?
            WHERE id=?""",
            (int(time.time()), score, TOTAL, a["id"])
        )
        d.commit()
    else:
        score = a["score"]

    # Foydalanuvchiga faqat umumiy natija beriladi.
    return jsonify(
        score=score,
        total=TOTAL,
        percent=round(score * 100 / TOTAL)
    )

