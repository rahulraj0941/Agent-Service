import json
from pathlib import Path
from typing import List, Dict, Any
from backend.rag.embeddings import EmbeddingService
from backend.rag.vector_store import VectorStore


class FAQRetrieval:
    def __init__(self, clinic_info_path: str = "data/clinic_info.json"):
        self.clinic_info_path = Path(clinic_info_path)
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        
        if self.vector_store.count() == 0:
            self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self) -> None:
        with open(self.clinic_info_path, 'r') as f:
            clinic_data = json.load(f)
        
        documents = []
        metadatas = []
        
        clinic_details = clinic_data.get("clinic_details", {})
        documents.append(
            f"Clinic Name: {clinic_details.get('name', '')}\n"
            f"Address: {clinic_details.get('address', '')}\n"
            f"Phone: {clinic_details.get('phone', '')}\n"
            f"Email: {clinic_details.get('email', '')}\n"
            f"Hours: {json.dumps(clinic_details.get('hours', {}), indent=2)}"
        )
        metadatas.append({"category": "clinic_details", "subcategory": "contact_and_hours"})
        
        documents.append(
            f"Directions: {clinic_details.get('directions', '')}"
        )
        metadatas.append({"category": "clinic_details", "subcategory": "directions"})
        
        documents.append(
            f"Parking Information: {clinic_details.get('parking', '')}"
        )
        metadatas.append({"category": "clinic_details", "subcategory": "parking"})
        
        insurance = clinic_data.get("insurance_and_billing", {})
        documents.append(
            f"Accepted Insurance Providers: {', '.join(insurance.get('accepted_insurance', []))}"
        )
        metadatas.append({"category": "insurance_billing", "subcategory": "insurance"})
        
        documents.append(
            f"Payment Methods: {', '.join(insurance.get('payment_methods', []))}\n"
            f"Billing Policy: {insurance.get('billing_policy', '')}"
        )
        metadatas.append({"category": "insurance_billing", "subcategory": "payment"})
        
        documents.append(
            f"Cancellation Fee: {insurance.get('cancellation_fee', '')}"
        )
        metadatas.append({"category": "insurance_billing", "subcategory": "cancellation_fee"})
        
        visit_prep = clinic_data.get("visit_preparation", {})
        documents.append(
            f"First Visit Documents Required:\n" + 
            "\n".join([f"- {doc}" for doc in visit_prep.get('first_visit_documents', [])])
        )
        metadatas.append({"category": "visit_preparation", "subcategory": "first_visit"})
        
        documents.append(
            f"What to Bring to Your Appointment:\n" + 
            "\n".join([f"- {item}" for item in visit_prep.get('what_to_bring', [])])
        )
        metadatas.append({"category": "visit_preparation", "subcategory": "what_to_bring"})
        
        documents.append(
            f"Arrival Time: {visit_prep.get('arrival_time', '')}"
        )
        metadatas.append({"category": "visit_preparation", "subcategory": "arrival"})
        
        policies = clinic_data.get("policies", {})
        for policy_name, policy_text in policies.items():
            documents.append(
                f"{policy_name.replace('_', ' ').title()}: {policy_text}"
            )
            metadatas.append({"category": "policies", "subcategory": policy_name})
        
        appt_types = clinic_data.get("appointment_types", {})
        for appt_type, details in appt_types.items():
            documents.append(
                f"Appointment Type: {appt_type.replace('_', ' ').title()}\n"
                f"Duration: {details.get('duration', '')} minutes\n"
                f"Description: {details.get('description', '')}\n"
                f"Cost: {details.get('cost_range', '')}"
            )
            metadatas.append({"category": "appointment_types", "subcategory": appt_type})
        
        common_q = clinic_data.get("common_questions", {})
        for question, answer in common_q.items():
            documents.append(
                f"Q: {question.replace('_', ' ').title()}?\nA: {answer}"
            )
            metadatas.append({"category": "common_questions", "subcategory": question})
        
        embeddings = self.embedding_service.embed_documents(documents)
        self.vector_store.add_documents(documents, metadatas, embeddings)
    
    def retrieve_relevant_info(self, query: str, top_k: int = 3) -> List[str]:
        query_embedding = self.embedding_service.embed_text(query)
        results = self.vector_store.query(query_embedding, n_results=top_k)
        
        return results["documents"]
    
    def get_context_for_query(self, query: str) -> str:
        relevant_docs = self.retrieve_relevant_info(query, top_k=3)
        
        if not relevant_docs:
            return "No relevant information found."
        
        context = "Here is relevant information from our clinic knowledge base:\n\n"
        for i, doc in enumerate(relevant_docs, 1):
            context += f"{i}. {doc}\n\n"
        
        return context.strip()
