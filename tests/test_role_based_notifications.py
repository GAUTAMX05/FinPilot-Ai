import sys
import os
import unittest

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.app.services.auth_service import auth_service
from src.app.services.notification_service import notification_service


class TestRoleBasedNotifications(unittest.TestCase):

    def setUp(self):
        # Reset notification service default notifications before each test
        notification_service._notifications = notification_service._init_default_notifications()
        self.cfo = auth_service.get_user_by_id("CFO-001")
        self.fm = auth_service.get_user_by_id("FIN-MGR-001")
        self.eng_head = auth_service.get_user_by_id("ENG-HEAD-001")
        self.mkt_head = auth_service.get_user_by_id("MKT-HEAD-001")
        self.auditor = auth_service.get_user_by_id("AUDITOR-001")

        self.assertIsNotNone(self.cfo, "CFO user must exist")
        self.assertIsNotNone(self.fm, "Finance Manager user must exist")
        self.assertIsNotNone(self.eng_head, "Engineering Head user must exist")
        self.assertIsNotNone(self.mkt_head, "Marketing Head user must exist")
        self.assertIsNotNone(self.auditor, "Auditor user must exist")

    def test_section_24_cfo_to_finance_manager_isolation(self):
        """
        CFO creates notification: recipientUserId = FIN-MGR-001
        Expected:
          CFO -> NOT in recipient inbox
          Finance Manager -> YES
          Engineering Head -> NO
          Auditor -> NO
        """
        notif = notification_service.send_notification(
            sender_user=self.cfo,
            recipient_user_id="FIN-MGR-001",
            type="APPROVAL_REQUEST",
            title="Review ₹85,000 Engineering Expense",
            message="Please review the ₹85,000 Engineering cloud expense.",
            priority="HIGH",
            entity_type="EXPENSE",
            entity_id="EXP-1021",
        )
        notif_id = notif["id"]

        # Check inboxes
        fm_inbox = notification_service.get_user_notifications(self.fm)["notifications"]
        cfo_inbox = notification_service.get_user_notifications(self.cfo)["notifications"]
        eng_inbox = notification_service.get_user_notifications(self.eng_head)["notifications"]
        aud_inbox = notification_service.get_user_notifications(self.auditor)["notifications"]

        fm_has = any(n["id"] == notif_id for n in fm_inbox)
        cfo_has = any(n["id"] == notif_id for n in cfo_inbox)
        eng_has = any(n["id"] == notif_id for n in eng_inbox)
        aud_has = any(n["id"] == notif_id for n in aud_inbox)

        self.assertTrue(fm_has, "Finance Manager MUST receive the notification in inbox")
        self.assertFalse(cfo_has, "CFO must NOT see sent notification in recipient inbox")
        self.assertFalse(eng_has, "Engineering Head must NOT see notification intended for Finance Manager")
        self.assertFalse(aud_has, "Auditor must NOT see notification intended for Finance Manager")

        # But CFO CAN see it in sent view
        cfo_sent = notification_service.get_user_notifications(self.cfo, view="sent")["notifications"]
        self.assertTrue(any(n["id"] == notif_id for n in cfo_sent), "CFO MUST be able to view sent notification in sent view")

    def test_section_24_fm_to_eng_head_isolation(self):
        """
        Finance Manager creates notification: recipientUserId = ENG-HEAD-001
        Expected:
          CFO -> NO
          Finance Manager -> NO
          Engineering Head -> YES
          Marketing Head -> NO
          Auditor -> NO
        """
        notif = notification_service.send_notification(
            sender_user=self.fm,
            recipient_user_id="ENG-HEAD-001",
            type="BUDGET_WARNING",
            title="Cloud Spend Justification Required",
            message="Please provide justification for the additional ₹200,000 cloud expense.",
            priority="HIGH",
            entity_type="BUDGET",
            entity_id="DEPT-ENG",
            department="Engineering",
        )
        notif_id = notif["id"]

        eng_inbox = notification_service.get_user_notifications(self.eng_head)["notifications"]
        mkt_inbox = notification_service.get_user_notifications(self.mkt_head)["notifications"]
        fm_inbox = notification_service.get_user_notifications(self.fm)["notifications"]
        cfo_inbox = notification_service.get_user_notifications(self.cfo)["notifications"]
        aud_inbox = notification_service.get_user_notifications(self.auditor)["notifications"]

        self.assertTrue(any(n["id"] == notif_id for n in eng_inbox), "Engineering Head MUST receive the notification")
        self.assertFalse(any(n["id"] == notif_id for n in mkt_inbox), "Marketing Head must NOT receive Engineering notification")
        self.assertFalse(any(n["id"] == notif_id for n in fm_inbox), "Finance Manager must NOT receive sent notification in inbox")
        self.assertFalse(any(n["id"] == notif_id for n in cfo_inbox), "CFO must NOT receive notification intended for Engineering Head")
        self.assertFalse(any(n["id"] == notif_id for n in aud_inbox), "Auditor must NOT receive notification intended for Engineering Head")

    def test_section_24_fm_to_auditor_isolation(self):
        """
        Finance Manager creates notification: recipientUserId = AUDITOR-001
        Expected:
          CFO -> NO
          Finance Manager -> NO
          Engineering Head -> NO
          Auditor -> YES
        """
        notif = notification_service.send_notification(
            sender_user=self.fm,
            recipient_user_id="AUDITOR-001",
            type="AUDIT_ASSIGNMENT",
            title="Audit Review Required: Invoice INV-1029",
            message="Invoice INV-1029 has a potential duplicate.",
            priority="CRITICAL",
            entity_type="INVOICE",
            entity_id="INV-1029",
        )
        notif_id = notif["id"]

        aud_inbox = notification_service.get_user_notifications(self.auditor)["notifications"]
        eng_inbox = notification_service.get_user_notifications(self.eng_head)["notifications"]
        cfo_inbox = notification_service.get_user_notifications(self.cfo)["notifications"]
        fm_inbox = notification_service.get_user_notifications(self.fm)["notifications"]

        self.assertTrue(any(n["id"] == notif_id for n in aud_inbox), "Auditor MUST receive the audit notification")
        self.assertFalse(any(n["id"] == notif_id for n in eng_inbox), "Engineering Head must NOT receive audit assignment")
        self.assertFalse(any(n["id"] == notif_id for n in cfo_inbox), "CFO must NOT receive audit assignment in recipient inbox")
        self.assertFalse(any(n["id"] == notif_id for n in fm_inbox), "Finance Manager must NOT receive sent notification in inbox")

    def test_two_way_communication_threading(self):
        """
        Tests the 2-way conversation request thread between CFO and Finance Manager:
        1. CFO sends request.
        2. Finance Manager replies.
        3. CFO replies back.
        4. Finance Manager marks as resolved.
        """
        # Step 1: CFO sends request
        notif = notification_service.send_notification(
            sender_user=self.cfo,
            recipient_user_id="FIN-MGR-001",
            type="APPROVAL_REQUEST",
            title="Engineering Cloud Spending",
            message="Please review the recent increase.",
            priority="HIGH",
            entity_type="EXPENSE",
            entity_id="EXP-1021",
        )
        notif_id = notif["id"]

        # Step 2: Finance Manager replies
        reply_res1 = notification_service.reply_to_thread(
            notification_id=notif_id,
            sender_user=self.fm,
            message="The increase is related to the new production deployment."
        )
        self.assertTrue(reply_res1["success"])
        self.assertEqual(len(reply_res1["thread"]), 2)

        # Step 3: CFO replies back
        reply_res2 = notification_service.reply_to_thread(
            notification_id=notif_id,
            sender_user=self.cfo,
            message="Please proceed with the revised budget."
        )
        self.assertTrue(reply_res2["success"])
        self.assertEqual(len(reply_res2["thread"]), 3)
        self.assertEqual(reply_res2["thread"][-1]["senderUserId"], "CFO-001")

        # Step 4: Finance Manager marks resolved
        resolve_res = notification_service.resolve_notification(
            notification_id=notif_id,
            user_id="FIN-MGR-001",
            user_name="Rahul Verma",
            user_role="FINANCE_MANAGER",
            resolution_note="Executed budget review and committed allocation."
        )
        self.assertTrue(resolve_res["success"])
        self.assertEqual(resolve_res["notification"]["status"], "RESOLVED")

    def test_observer_cc_support(self):
        """
        Tests that explicitly specified observers in observerIds can see the notification,
        while non-observers cannot.
        """
        notif = notification_service.send_notification(
            sender_user=self.cfo,
            recipient_user_id="FIN-MGR-001",
            type="APPROVAL_REQUEST",
            title="Special Procurement Request",
            message="Evaluating vendor contracts with observer oversight.",
            priority="HIGH",
            observer_ids=["AUDITOR-001"] # Auditor is CC'd
        )
        notif_id = notif["id"]

        fm_inbox = notification_service.get_user_notifications(self.fm)["notifications"]
        aud_inbox = notification_service.get_user_notifications(self.auditor)["notifications"]
        eng_inbox = notification_service.get_user_notifications(self.eng_head)["notifications"]

        self.assertTrue(any(n["id"] == notif_id for n in fm_inbox), "Primary recipient FM MUST receive notification")
        self.assertTrue(any(n["id"] == notif_id for n in aud_inbox), "CC'd Auditor MUST receive notification")
        self.assertFalse(any(n["id"] == notif_id for n in eng_inbox), "Unrelated Dept Head MUST NOT receive notification")

    def test_escalation_to_cfo(self):
        """
        Tests escalating an open notification to the CFO:
        Recipient changes to CFO-001, priority becomes CRITICAL, status becomes ESCALATED.
        """
        notif = notification_service.send_notification(
            sender_user=self.eng_head,
            recipient_user_id="FIN-MGR-001",
            type="BUDGET_REQUEST",
            title="Additional Server Budget",
            message="Requesting ₹300,000 additional budget.",
            priority="MEDIUM",
        )
        notif_id = notif["id"]

        esc_res = notification_service.escalate_notification(
            notification_id=notif_id,
            user_id="FIN-MGR-001",
            user_name="Rahul Verma",
            user_role="FINANCE_MANAGER",
            escalation_reason="Exceeds manager threshold; requires CFO sign-off."
        )
        self.assertTrue(esc_res["success"])
        self.assertEqual(esc_res["notification"]["recipientUserId"], "CFO-001")
        self.assertEqual(esc_res["notification"]["priority"], "CRITICAL")
        self.assertEqual(esc_res["notification"]["status"], "ESCALATED")

        # Verify CFO inbox now has it
        cfo_inbox = notification_service.get_user_notifications(self.cfo)["notifications"]
        self.assertTrue(any(n["id"] == notif_id for n in cfo_inbox), "CFO inbox MUST now have the escalated notification")

    def test_communication_directory_routing_rules(self):
        """
        Tests role-based communication directory rules:
        - CFO: can message anyone
        - Dept Head: can only message FM and CFO (no lateral messaging to Marketing Head)
        """
        cfo_dir = auth_service.get_directory_for_user(self.cfo)
        cfo_roles = {u["role"] for u in cfo_dir}
        self.assertIn("FINANCE_MANAGER", cfo_roles)
        self.assertIn("DEPARTMENT_HEAD", cfo_roles)
        self.assertIn("AUDITOR", cfo_roles)

        eng_dir = auth_service.get_directory_for_user(self.eng_head)
        eng_roles = {u["role"] for u in eng_dir}
        self.assertIn("FINANCE_MANAGER", eng_roles)
        self.assertIn("CFO", eng_roles)
        self.assertNotIn("AUDITOR", eng_roles)
        self.assertFalse(any(u["id"] == "MKT-HEAD-001" for u in eng_dir), "Engineering Head cannot message Marketing Head directly")


if __name__ == "__main__":
    print("==================================================================")
    print("   FINPILOT AI — ROLE-BASED NOTIFICATION SECURITY TEST SUITE     ")
    print("==================================================================")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRoleBasedNotifications)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\n==================================================================")
        print("ALL ROLE-BASED NOTIFICATION SECURITY & ISOLATION TESTS PASSED 100%!")
        print("==================================================================")
    else:
        sys.exit(1)
