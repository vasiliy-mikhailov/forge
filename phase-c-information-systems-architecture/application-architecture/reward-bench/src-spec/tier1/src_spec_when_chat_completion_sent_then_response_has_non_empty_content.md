# `src_spec_when_chat_completion_sent_then_response_has_non_empty_content`

Lab vLLM container accepts standard OpenAI-style `POST
/v1/chat/completions` requests and returns a `choices[0].message.content`
string for any well-formed payload.

No bench-side implementation in `src/`; the bench just builds the
HTTP request, parses the JSON, and checks the content field.
