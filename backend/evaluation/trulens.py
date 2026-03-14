from trulens_eval import Tru
from trulens_eval.feedback import Feedback
from trulens_eval.feedback.provider.openai import OpenAI

tru = Tru()

provider = OpenAI()

f_relevance = Feedback(provider.relevance)

print("Evaluation ready")