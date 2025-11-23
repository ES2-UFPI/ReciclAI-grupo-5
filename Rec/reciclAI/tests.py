from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Residue, Profile, Collection, Reward


class UserCreationTest(TestCase):
    def test_user_and_profile_creation(self):
        user = User.objects.create_user(username="testuser", password="password")
        self.assertIsNotNone(user.profile)
        self.assertEqual(user.profile.user_type, "C")


class CitizenFlowTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="citizen", password="password")
        self.user.profile.user_type = "C"
        self.user.profile.save()
        self.client.login(username="citizen", password="password")

    def test_create_residue_and_request_collection(self):
        self.client.post(
            reverse("reciclAI:residue_create"),
            {
                "residue_type": "Garrafa PET",
                "units": 10,
                "location": "Rua dos Testes, 123",
            },
        )
        residue = Residue.objects.get(citizen=self.user)
        self.assertEqual(residue.status, "AGUARDANDO_SOLICITACAO_DE_COLETA")

        self.client.post(reverse("reciclAI:request_collection", args=[residue.id]))
        residue.refresh_from_db()
        self.assertEqual(residue.status, "COLETA_SOLICITADA")
        self.assertIsNotNone(residue.collection)
        self.assertEqual(residue.collection.status, "SOLICITADA")


class CollectorFlowTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.citizen = User.objects.create_user(username="citizen", password="password")
        self.collector = User.objects.create_user(
            username="collector", password="password"
        )
        self.collector.profile.user_type = "L"
        self.collector.profile.save()
        self.residue = Residue.objects.create(
            citizen=self.citizen,
            residue_type="Papelão",
            weight=5,
            location="Av. Brasil",
        )
        self.collection = Collection.objects.create(residue=self.residue)
        self.client.login(username="collector", password="password")

    def test_accept_collection(self):
        self.client.post(
            reverse("reciclAI:accept_collection", args=[self.collection.id])
        )
        self.collection.refresh_from_db()
        self.assertEqual(self.collection.status, "ATRIBUIDA")
        self.assertEqual(self.collection.collector, self.collector)

    def test_update_collection_status(self):
        self.collection.collector = self.collector
        self.collection.status = "ATRIBUIDA"
        self.collection.save()

        self.client.post(
            reverse("reciclAI:collection_transition", args=[self.collection.id]),
            {"status": "EM_ROTA"},
        )
        self.collection.refresh_from_db()
        self.assertEqual(self.collection.status, "EM_ROTA")

        self.client.post(
            reverse("reciclAI:collection_transition", args=[self.collection.id]),
            {"status": "COLETADA"},
        )
        self.collection.refresh_from_db()
        self.assertEqual(self.collection.status, "COLETADA")

        self.client.post(
            reverse("reciclAI:collection_transition", args=[self.collection.id]),
            {"status": "ENTREGUE_RECICLADORA"},
        )
        self.collection.refresh_from_db()
        self.assertEqual(self.collection.status, "ENTREGUE_RECICLADORA")


class RecyclerFlowTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.citizen = User.objects.create_user(username="citizen", password="password")
        self.recycler = User.objects.create_user(
            username="recycler", password="password"
        )
        self.recycler.profile.user_type = "R"
        self.recycler.profile.save()
        self.residue = Residue.objects.create(
            citizen=self.citizen, residue_type="Vidro", units=20, location="Praça da Sé"
        )
        self.collection = Collection.objects.create(
            residue=self.residue, status="ENTREGUE_RECICLADORA"
        )
        self.client.login(username="recycler", password="password")

    def test_process_collection_and_award_points(self):
        self.client.post(
            reverse("reciclAI:process_collection", args=[self.collection.id])
        )
        self.collection.refresh_from_db()
        self.assertEqual(self.collection.status, "PROCESSADO")
        self.residue.refresh_from_db()
        self.assertEqual(self.residue.status, "PROCESSADO")
        self.citizen.profile.refresh_from_db()
        self.assertEqual(self.citizen.profile.points, 10)


class PointsAndRewardsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="citizen", password="password")
        self.user.profile.points = 100
        self.user.profile.save()
        self.reward = Reward.objects.create(name="Voucher", points_required=50)
        self.client.login(username="citizen", password="password")

    def test_redeem_reward(self):
        self.client.post(reverse("reciclAI:redeem_reward", args=[self.reward.id]))
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.points, 50)

    def test_insufficient_points(self):
        self.user.profile.points = 20
        self.user.profile.save()
        self.client.post(reverse("reciclAI:redeem_reward", args=[self.reward.id]))
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.points, 20)
