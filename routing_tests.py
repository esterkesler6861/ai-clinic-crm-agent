from uuid import uuid4

from dotenv import load_dotenv

load_dotenv()

from graph import graph


DEFAULT_ROUTING_TESTS = [

    # =========================
    # BOOK APPOINTMENT
    # =========================

    {"input": "אני רוצה לקבוע תור", "expected_intent": "book_appointment"},
    {"input": "תור", "expected_intent": "book_appointment"},
    {"input": "יש תורים?", "expected_intent": "book_appointment"},
    {"input": "אפשר תור להיום?", "expected_intent": "book_appointment"},
    {"input": "צריכה רופא", "expected_intent": "book_appointment"},
    {"input": "צריכה ילדים", "expected_intent": "book_appointment"},
    {"input": "רופא ילדים", "expected_intent": "book_appointment"},
    {"input": "רופא משפחה", "expected_intent": "book_appointment"},
    {"input": "קרדיולוג", "expected_intent": "book_appointment"},
    {"input": "אורתופד", "expected_intent": "book_appointment"},
    {"input": "רופא עור", "expected_intent": "book_appointment"},
    {"input": "לב לילד", "expected_intent": "book_appointment"},
    {"input": "משפחה היום", "expected_intent": "book_appointment"},
    {"input": "אני רוצה לקבוע ולא לבטל", "expected_intent": "book_appointment"},

    # =========================
    # CANCEL APPOINTMENT
    # =========================

    {"input": "אני רוצה לבטל תור", "expected_intent": "cancel_appointment"},
    {"input": "לבטל", "expected_intent": "cancel_appointment"},
    {"input": "ביטול תור", "expected_intent": "cancel_appointment"},
    {"input": "תבטלי לי", "expected_intent": "cancel_appointment"},
    {"input": "לא צריכה את התור", "expected_intent": "cancel_appointment"},
    {"input": "תמחקי את התור שלי", "expected_intent": "cancel_appointment"},
    {"input": "לבטל את מה שקבעתי", "expected_intent": "cancel_appointment"},

    # =========================
    # REFERRAL STATUS
    # =========================

    {"input": "מה סטטוס הפניה 700", "expected_intent": "referral_status"},
    {"input": "הפניה", "expected_intent": "referral_status"},
    {"input": "סטטוס הפניה", "expected_intent": "referral_status"},
    {"input": "מה עם ההפניה שלי", "expected_intent": "referral_status"},
    {"input": "אני מחכה להפניה", "expected_intent": "referral_status"},
    {"input": "הפניה 701", "expected_intent": "referral_status"},

    # =========================
    # FORM 17
    # =========================

    {"input": "מה עם טופס 17 מספר 801", "expected_intent": "form17_status"},
    {"input": "טופס 17", "expected_intent": "form17_status"},
    {"input": "התחייבות", "expected_intent": "form17_status"},
    {"input": "בדיקת התחייבות", "expected_intent": "form17_status"},
    {"input": "אישור התחייבות", "expected_intent": "form17_status"},
    {"input": "מחכה לטופס 17", "expected_intent": "form17_status"},

    # =========================
    # HUMAN ESCALATION
    # =========================

    {"input": "אני רוצה לדבר עם מזכירה", "expected_intent": "human_escalation"},
    {"input": "מזכירה", "expected_intent": "human_escalation"},
    {"input": "נציג", "expected_intent": "human_escalation"},
    {"input": "מענה אנושי", "expected_intent": "human_escalation"},
    {"input": "אפשר לדבר עם בן אדם?", "expected_intent": "human_escalation"},
    {"input": "אין לי כוח לבוט", "expected_intent": "human_escalation"},
    {"input": "דחוף", "expected_intent": "human_escalation"},

    # =========================
    # GENERAL FEEDBACK
    # =========================

    {"input": "תודה", "expected_intent": "general_feedback"},
    {"input": "תודה רבה", "expected_intent": "general_feedback"},
    {"input": "מעולה", "expected_intent": "general_feedback"},
    {"input": "איזה שירות טוב", "expected_intent": "general_feedback"},
    {"input": "היי", "expected_intent": "general_feedback"},

    # =========================
    # UNSUPPORTED TOPIC
    # =========================

    {"input": "מה מזג האוויר", "expected_intent": "unsupported_topic"},
    {"input": "ספרי בדיחה", "expected_intent": "unsupported_topic"},
    {"input": "כמה זה 2+2", "expected_intent": "unsupported_topic"},
    {"input": "איך מכינים פסטה", "expected_intent": "unsupported_topic"},

    # =========================
    # UNKNOWN
    # =========================

    {"input": "יש משהו", "expected_intent": "unknown"},
    {"input": "אפשר?", "expected_intent": "unknown"},
    {"input": "תעזרי לי", "expected_intent": "unknown"},
    {"input": "בעיה", "expected_intent": "unknown"},
    {"input": "לא יודעת", "expected_intent": "unknown"},
    {"input": "מה עושים", "expected_intent": "unknown"},
]


def run_routing_tests(test_cases=None):

    tests = test_cases or DEFAULT_ROUTING_TESTS

    results = []
    passed = 0

    # IMPORTANT:
    # creates a unique run id so tests do not reuse old checkpoints
    run_id = str(uuid4())

    for index, test in enumerate(tests, start=1):

        user_input = test.get("input", "")
        expected_intent = test.get("expected_intent")

        result = graph.invoke(
            {
                "user_input": user_input,
                "messages": [
                    {
                        "role": "user",
                        "content": user_input
                    }
                ],
            },
            config={
                "configurable": {
                    "thread_id": f"routing-dashboard-{run_id}-test-{index}"
                }
            },
        )

        actual_intent = result.get("intent")

        success = actual_intent == expected_intent

        if success:
            passed += 1

        results.append({
            "index": index,
            "input": user_input,
            "expected_intent": expected_intent,
            "actual_intent": actual_intent,
            "success": success,
            "answer": result.get("answer"),
            "decision_summary": result.get("decision_summary"),
            "logs": result.get("logs") or [],
            "state": {
                "intent": result.get("intent"),
                "active_flow": result.get("active_flow"),
                "waiting_for_specialty": result.get("waiting_for_specialty"),
                "waiting_for_time_selection": result.get("waiting_for_time_selection"),
                "waiting_for_confirmation": result.get("waiting_for_confirmation"),
                "specialty": result.get("specialty"),
                "selected_slot": result.get("selected_slot"),
            }
        })

    return {
        "total": len(tests),
        "passed": passed,
        "failed": len(tests) - passed,
        "success_rate": round((passed / len(tests)) * 100, 2) if tests else 0,
        "results": results,
    }


if __name__ == "__main__":

    summary = run_routing_tests()

    print("=" * 70)
    print(f"PASSED: {summary['passed']}/{summary['total']}")
    print(f"SUCCESS RATE: {summary['success_rate']}%")

    failed = [x for x in summary["results"] if not x["success"]]

    if failed:

        print("\nFAILED TESTS")
        print("=" * 70)

        for item in failed:

            print(f"\nINPUT: {item['input']}")
            print(f"EXPECTED: {item['expected_intent']}")
            print(f"ACTUAL: {item['actual_intent']}")
            print(f"ANSWER: {item['answer']}")
            print(f"DECISION SUMMARY: {item['decision_summary']}")

            print("-" * 50)