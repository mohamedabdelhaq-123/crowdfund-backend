from django.test import TestCase
from django.urls import reverse, resolve
from django.apps import apps
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import Tag
from .serializer import TagSerializer
from .views import TagViewSet


class TagModelTest(TestCase):
    def test_create_tag(self):
        tag = Tag.objects.create(name="django")
        self.assertEqual(tag.name, "django")
        self.assertIsNotNone(tag.id)

    def test_created_at_auto_set(self):
        tag = Tag.objects.create(name="python")
        self.assertIsNotNone(tag.created_at)

    def test_name_max_length_field_constraint(self):
        field = Tag._meta.get_field("name")
        self.assertEqual(field.max_length, 100)

    def test_name_at_exact_max_length_accepted(self):
        long_name = "a" * 100
        tag = Tag.objects.create(name=long_name)
        self.assertEqual(tag.name, long_name)

    def test_primary_key_is_bigautofield(self):
        field = Tag._meta.get_field("id")
        self.assertEqual(field.get_internal_type(), "BigAutoField")

    def test_created_at_is_auto_now_add(self):
        field = Tag._meta.get_field("created_at")
        self.assertTrue(field.auto_now_add)

    def test_duplicate_names_allowed(self):
        # model has no unique constraint on name
        tag1 = Tag.objects.create(name="shared")
        tag2 = Tag.objects.create(name="shared")
        self.assertNotEqual(tag1.id, tag2.id)
        self.assertEqual(Tag.objects.filter(name="shared").count(), 2)

    def test_tag_name_with_special_characters(self):
        tag = Tag.objects.create(name="tag-with_special.chars")
        self.assertEqual(tag.name, "tag-with_special.chars")

    def test_string_representation_contains_pk(self):
        tag = Tag.objects.create(name="test-tag")
        # No custom __str__; default Django representation includes pk
        self.assertIn(str(tag.pk), str(tag))

    def test_insertion_order_preserved(self):
        tag1 = Tag.objects.create(name="first")
        tag2 = Tag.objects.create(name="second")
        tags = list(Tag.objects.order_by("id"))
        self.assertEqual(tags[0].id, tag1.id)
        self.assertEqual(tags[1].id, tag2.id)


class TagSerializerTest(TestCase):
    def test_serializes_all_three_fields(self):
        tag = Tag.objects.create(name="serialized")
        serializer = TagSerializer(tag)
        self.assertSetEqual(set(serializer.data.keys()), {"id", "name", "created_at"})

    def test_serialized_name_value(self):
        tag = Tag.objects.create(name="my-tag")
        serializer = TagSerializer(tag)
        self.assertEqual(serializer.data["name"], "my-tag")

    def test_serialized_id_matches_pk(self):
        tag = Tag.objects.create(name="pk-check")
        serializer = TagSerializer(tag)
        self.assertEqual(serializer.data["id"], tag.pk)

    def test_deserializes_valid_data(self):
        data = {"name": "new-tag"}
        serializer = TagSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_save_creates_tag(self):
        data = {"name": "saved-tag"}
        serializer = TagSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        tag = serializer.save()
        self.assertIsNotNone(tag.id)
        self.assertEqual(tag.name, "saved-tag")

    def test_missing_name_is_invalid(self):
        serializer = TagSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_name_exceeding_max_length_is_invalid(self):
        data = {"name": "x" * 101}
        serializer = TagSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_name_at_exact_max_length_is_valid(self):
        data = {"name": "b" * 100}
        serializer = TagSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_created_at_ignored_on_write(self):
        # created_at is auto_now_add so any supplied value should be ignored
        data = {"name": "tag", "created_at": "2020-01-01T00:00:00Z"}
        serializer = TagSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        tag = serializer.save()
        self.assertIsNotNone(tag.created_at)

    def test_empty_name_is_invalid(self):
        serializer = TagSerializer(data={"name": ""})
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)


class TagViewSetTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.list_url = "/tags/"

    def test_list_tags_returns_200(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_tags_returns_all_tags(self):
        Tag.objects.create(name="alpha")
        Tag.objects.create(name="beta")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        # Support both plain list and paginated response
        items = data if isinstance(data, list) else data.get("results", data)
        self.assertEqual(len(items), 2)

    def test_list_tags_empty_db(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        items = data if isinstance(data, list) else data.get("results", [])
        self.assertEqual(len(items), 0)

    def test_create_tag_returns_201(self):
        response = self.client.post(self.list_url, {"name": "new-tag"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_tag_response_contains_fields(self):
        response = self.client.post(self.list_url, {"name": "new-tag"}, format="json")
        self.assertEqual(response.data["name"], "new-tag")
        self.assertIn("id", response.data)
        self.assertIn("created_at", response.data)

    def test_create_tag_persists_to_db(self):
        self.client.post(self.list_url, {"name": "persisted"}, format="json")
        self.assertTrue(Tag.objects.filter(name="persisted").exists())

    def test_create_tag_missing_name_returns_400(self):
        response = self.client.post(self.list_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_create_tag_name_too_long_returns_400(self):
        response = self.client.post(
            self.list_url, {"name": "x" * 101}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tag_returns_200(self):
        tag = Tag.objects.create(name="retrieve-me")
        response = self.client.get(f"/tags/{tag.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "retrieve-me")
        self.assertEqual(response.data["id"], tag.pk)

    def test_retrieve_nonexistent_tag_returns_404(self):
        response = self.client.get("/tags/9999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_tag_returns_200(self):
        tag = Tag.objects.create(name="old-name")
        response = self.client.put(
            f"/tags/{tag.pk}/", {"name": "new-name"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "new-name")

    def test_update_tag_persists_to_db(self):
        tag = Tag.objects.create(name="old-name")
        self.client.put(f"/tags/{tag.pk}/", {"name": "new-name"}, format="json")
        tag.refresh_from_db()
        self.assertEqual(tag.name, "new-name")

    def test_partial_update_tag(self):
        tag = Tag.objects.create(name="partial-old")
        response = self.client.patch(
            f"/tags/{tag.pk}/", {"name": "partial-new"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "partial-new")

    def test_delete_tag_returns_204(self):
        tag = Tag.objects.create(name="delete-me")
        response = self.client.delete(f"/tags/{tag.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_tag_removes_from_db(self):
        tag = Tag.objects.create(name="delete-me")
        self.client.delete(f"/tags/{tag.pk}/")
        self.assertFalse(Tag.objects.filter(pk=tag.pk).exists())

    def test_delete_nonexistent_tag_returns_404(self):
        response = self.client.delete("/tags/9999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_with_empty_name_returns_400(self):
        tag = Tag.objects.create(name="valid")
        response = self.client.put(
            f"/tags/{tag.pk}/", {"name": ""}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TagURLRoutingTest(TestCase):
    def test_tags_list_url_resolves_to_viewset(self):
        resolver = resolve("/tags/")
        self.assertEqual(resolver.func.cls, TagViewSet)

    def test_tags_detail_url_resolves_to_viewset(self):
        tag = Tag.objects.create(name="url-test")
        resolver = resolve(f"/tags/{tag.pk}/")
        self.assertEqual(resolver.func.cls, TagViewSet)

    def test_tags_list_reverse_url(self):
        url = reverse("tag-list")
        self.assertEqual(url, "/tags/")

    def test_tags_detail_reverse_url(self):
        tag = Tag.objects.create(name="detail-url")
        url = reverse("tag-detail", kwargs={"pk": tag.pk})
        self.assertEqual(url, f"/tags/{tag.pk}/")


class TagAdminTest(TestCase):
    def test_tag_registered_in_admin(self):
        from django.contrib import admin as django_admin
        self.assertIn(Tag, django_admin.site._registry)

    def test_admin_model_admin_instance_exists(self):
        from django.contrib import admin as django_admin
        model_admin = django_admin.site._registry.get(Tag)
        self.assertIsNotNone(model_admin)


class TagAppConfigTest(TestCase):
    def test_app_config_name(self):
        app_config = apps.get_app_config("tag")
        self.assertEqual(app_config.name, "apps.tag")

    def test_app_config_default_auto_field(self):
        app_config = apps.get_app_config("tag")
        self.assertEqual(
            app_config.default_auto_field, "django.db.models.BigAutoField"
        )

    def test_app_config_label(self):
        app_config = apps.get_app_config("tag")
        self.assertEqual(app_config.label, "tag")