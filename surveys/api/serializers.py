from rest_framework import serializers

from surveys.models import Choice, Question, Survey


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ('id', 'text', 'position', 'allows_free_text')


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ('id', 'text', 'position', 'choices')


class ChoiceWriteSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=500)
    position = serializers.IntegerField(min_value=0)
    allows_free_text = serializers.BooleanField(default=False)


class QuestionWriteSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=500)
    position = serializers.IntegerField(min_value=0)
    choices = ChoiceWriteSerializer(many=True)


class SurveySerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.username', read_only=True)
    questions_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Survey
        fields = ('id', 'title', 'author', 'created_at', 'questions_count')


class SurveyPatchSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, trim_whitespace=True)


class SurveyCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, trim_whitespace=True)
    questions = QuestionWriteSerializer(many=True)

    def validate_questions(self, value):
        if not value:
            raise serializers.ValidationError('Опрос должен содержать хотя бы один вопрос.')

        positions = [question['position'] for question in value]
        if len(positions) != len(set(positions)):
            raise serializers.ValidationError('Позиции вопросов должны быть уникальными.')

        for question in value:
            if not question['choices']:
                raise serializers.ValidationError(
                    f'Вопрос {question["text"]} должен содержать хотя бы один вариант ответа.',
                )

            choice_position = [choice['position'] for choice in question['choices']]
            if len(choice_position) != len(set(choice_position)):
                raise serializers.ValidationError(
                    f'Позиции вариантов ответа должны быть уникальными в вопросе {question["text"]}.',
                )
        return value


class AnswerWriteSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    choice_id = serializers.IntegerField()
    free_text = serializers.CharField(
        max_length=1000, required=False, allow_blank=True, default=''
    )
