# AI4Bharat Svarah — Indian-accented English speech dataset
#
# This folder is for evaluation and documentation of Indian English speech.
# The chatbot's live microphone path uses the **browser Web Speech API**.
# Web Speech API was NOT trained on Svarah in this project.
#
# Official sources:
#   Paper:  https://arxiv.org/abs/2305.15760
#   GitHub: https://github.com/AI4Bharat/Svarah
#   Site:   https://ai4bharat.iitm.ac.in/svarah (if available)
#
# Audio is large and licensed by the dataset authors. It is not vendored here.
# Place downloaded clips under dataset/svarah/audio/ if you run your own ASR eval.

name: Svarah
provider: AI4Bharat
language: Indian English (L2), speakers with diverse L1 Indian languages
role_in_this_project: evaluation notes + Indian-English test phrases for the Web Speech UI
not_used_for: training the browser speech recognizer or the LSTM intent model
