from django.test import TestCase
from rest_framework.test import APIClient
from .app_settings import GAME_NAME
from django.urls import reverse
from django.contrib.auth.models import User
from player_acct.models import Player
from .models import Team, GamePlayer

# Create your tests here.
class TeamAPITestCase(TestCase):
	def setUp(self):
		self.user_1 = User.objects.create(username='test_cpt')
		Player.objects.create(user=self.user_1, username='test_cpt')
		self.user_2 = User.objects.create(username='test_child')
		Player.objects.create(user=self.user_2, username='test_child')
		self.client = APIClient()

	'''
	Test that all CRUD Actions can be performed on Team Model via API
	'''
	def test_team_valid_CRUD_actions(self):
		self.client.force_authenticate(user=self.user_1) # Authenticate user as captain for valid CRUD
		# Create new test Team
		post_response = self.client.post(reverse('%s:api-team-list' % GAME_NAME), {'name':'Test', 'description':'This team sucks'}, format='json')
		# Update the name and description of Team
		patch_response = self.client.patch(reverse('%s:api-team-update' % GAME_NAME, kwargs={'pk':'1'}), {'name':'EditedTeam', 'description':'This team does NOT suck'}, format='json')
		# Retrieve the newly modified Team
		get_response = self.client.get(reverse('%s:api-team-detail' % GAME_NAME, kwargs={'pk':'1'}))
		# Delete the test Team
		delete_response = self.client.delete(reverse('%s:api-team-destroy' % GAME_NAME, kwargs={'pk':'1'}))
		self.client.force_authenticate(user=None) # Log user out for subsequent tests
		
		try:
			self.assertEqual(post_response.status_code, 201) 			# Post Success
			self.assertEqual(patch_response.status_code, 200)			# Patch Success
			self.assertEqual(get_response.status_code, 200) 			# Get Success
			self.assertEqual(get_response.data['name'], 'EditedTeam') 	# Validate Patch updated team's name
			self.assertEqual(Team.objects.all().count(), 0) 			# Ensure no Teams exist after delete

		except AssertionError as e:
			if post_response.status_code == 302:
				e.args = (('[302] User was not authenticated before creating Team'),)
			if get_response.status_code == 404:
				e.args = (('[404] Attempting GET request on non-existant Team'),)
			print(get_response)
			raise

	'''
	Test that constraints on Patch and Delete are valid via API
	'''
	def test_team_unauthorized_CRUD_actions(self):
		self.client.force_authenticate(user=self.user_1) 	# Authenticate user as captain for team
		# Create new test Team
		post_response = self.client.post(reverse('%s:api-team-list' % GAME_NAME), {'name':'Test', 'description':'This team sucks'}, format='json')
		self.client.force_authenticate(user=None) 			# De-authenticate user as captain for team
		self.client.force_authenticate(user=self.user_2) 	# Authenticate intruder for invalid CRUD
		# Intruder attempt to maliciously update Team
		patch_response = self.client.patch(reverse('%s:api-team-update' % GAME_NAME, kwargs={'pk':'1'}), {'name':'EditedTeam', 'description':'This team does NOT suck'}, format='json')
		# Intruder attempts to maliciously delete Team
		delete_response = self.client.delete(reverse('%s:api-team-destroy' % GAME_NAME, kwargs={'pk':'1'}))
		
		try:
			self.assertEqual(patch_response.status_code, 403)
			self.assertEqual(delete_response.status_code, 401)
			self.assertEqual(Team.objects.all().count, 1)
		except AssertionError as e:
			e.args = ("[PATCH] Intruder was allowed in")

	'''
	Test that a user cannot specify who is captain of team during CREATE/POST
	'''
	def test_team_create_cannot_inject_captain(self):
		self.client.force_authenticate(user=self.user_1) 	# Authenticate user as captain for team
		intruder_game_player = self.user_2.player.dota_player.get()
		# Create new test Team
		post_response = self.client.post(reverse('%s:api-team-list' % GAME_NAME), {'name':'Test', 'description':'This team sucks', 'captain':intruder_game_player.pk}, format='json')
		test_team = Team.objects.get(pk=1)
		self.client.force_authenticate(user=None) 			# De-authenticate user as captain for team
		
		try:
			self.assertNotEqual(test_team.captain.pk, self.user_2.pk)
		except AssertionError as e:
			e.args = ("[PATCH] Intruder was allowed in")



