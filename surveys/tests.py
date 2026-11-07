from django.urls import reverse
from rest_framework.test import APITestCase

from surveys.models import Answer, Attempt, Choice, Question, Survey, User


class NextQuestionTests(APITestCase):
    def setUp(self):
        self.author = User.objects.create(username='author')
        self.user = User.objects.create(username='taker')
        self.survey = Survey.objects.create(title='Овощи', author=self.author)
        self.q1 = Question.objects.create(
            survey=self.survey,
            text='Огурцы?',
            position=1,
        )
        self.c1_yes = Choice.objects.create(
            question=self.q1,
            text='Да',
            position=1,
        )
        self.c1_no = Choice.objects.create(
            question=self.q1,
            text='Нет',
            position=2,
        )
        self.q2 = Question.objects.create(
            survey=self.survey,
            text='Свой вкус?',
            position=2,
        )
        self.c2_free = Choice.objects.create(
            question=self.q2,
            text='Свой ответ',
            position=1,
            allows_free_text=True,
        )
        self.c2_skip = Choice.objects.create(
            question=self.q2,
            text='Пропустить',
            position=2,
        )
        self.next_url = reverse(
            'surveys:api-next-question',
            kwargs={'survey_id': self.survey.id},
        )
        self.answer_url = reverse(
            'surveys:api-answer',
            kwargs={'survey_id': self.survey.id},
        )
        self.client.credentials()
        self.headers = {'HTTP_X_USER_ID': self.user.username}

    def test_next_question_follows_progress(self):
        r1 = self.client.get(self.next_url, **self.headers)
        self.assertEqual(r1.status_code, 200)
        self.assertFalse(r1.data['done'])
        self.assertEqual(r1.data['question']['id'], self.q1.id)
        self.assertEqual(r1.data['question']['position'], 1)
        r_ans = self.client.post(
            self.answer_url,
            {'question_id': self.q1.id, 'choice_id': self.c1_yes.id},
            format='json',
            **self.headers,
        )
        self.assertEqual(r_ans.status_code, 201)
        r2 = self.client.get(self.next_url, **self.headers)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data['question']['id'], self.q2.id)
        r_ans2 = self.client.post(
            self.answer_url,
            {
                'question_id': self.q2.id,
                'choice_id': self.c2_free.id,
                'free_text': 'только черри',
            },
            format='json',
            **self.headers,
        )
        self.assertEqual(r_ans2.status_code, 201)
        self.assertTrue(r_ans2.data['done'])
        r3 = self.client.get(self.next_url, **self.headers)
        self.assertTrue(r3.data['done'])
        self.assertIsNone(r3.data['question'])
        self.assertIsNotNone(r3.data['finished_at'])
        attempt = Attempt.objects.get(pk=r3.data['attempt_id'])
        self.assertEqual(Answer.objects.filter(attempt=attempt).count(), 2)

    def test_free_text_required_when_flagged(self):
        self.client.post(
            self.answer_url,
            {'question_id': self.q1.id, 'choice_id': self.c1_no.id},
            format='json',
            **self.headers,
        )
        bad = self.client.post(
            self.answer_url,
            {'question_id': self.q2.id, 'choice_id': self.c2_free.id, 'free_text': ''},
            format='json',
            **self.headers,
        )
        self.assertEqual(bad.status_code, 400)
        ok = self.client.post(
            self.answer_url,
            {
                'question_id': self.q2.id,
                'choice_id': self.c2_free.id,
                'free_text': 'хруст',
            },
            format='json',
            **self.headers,
        )
        self.assertEqual(ok.status_code, 201)
        ans = Answer.objects.get(choice=self.c2_free)
        self.assertEqual(ans.free_text, 'хруст')

    def test_api_requires_header(self):
        r = self.client.get(self.next_url)
        self.assertEqual(r.status_code, 401)
