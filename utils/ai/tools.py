from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    groq_api_key="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"
    # other params...
)

class Performance(BaseModel):
  summary:str
prompt="""You are a child evaluator of College. A student has been classified into cluster {cluster} and risk classification is {risk}. Given a report of performance on given fields {report}. Write a summary of overall performance of the child"""
prompt=PromptTemplate.from_template(prompt)
strengths_chain=prompt|llm.with_structured_output(Performance)
# from transformers import AutoModelForCausalLM, AutoTokenizer,pipeline
# from langchain_huggingface import ChatHuggingFace
# from langchain_huggingface import HuggingFacePipeline
# model_id = "meta-llama/Llama-3.2-1B-Instruct"
# tokenizer = AutoTokenizer.from_pretrained(model_id)

# model = AutoModelForCausalLM.from_pretrained(
#     model_id,device_map='cuda'
# )
# pipe = pipeline(task='text-generation',model=model, tokenizer=tokenizer, max_new_tokens=256, top_k=50, temperature=0.1)
# llm = HuggingFacePipeline(pipeline=pipe)
# llm_engine = ChatHuggingFace(llm=llm)



