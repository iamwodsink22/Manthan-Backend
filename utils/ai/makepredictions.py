import joblib
import pandas as pd
from sqlalchemy.dialects.postgresql import insert
from lime.lime_tabular import LimeTabularExplainer
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel
from langchain_groq import ChatGroq
import datetime
from utils.models import Student,StudentPredctions,SessionLocal

class RunPredictions():
    def __init__(self):
        self.db=SessionLocal()
        self.clusterer=joblib.load('./utils/ai/models/clusterer.joblib')
        self.classifier=joblib.load('./utils/ai/models/risk_classifier.joblib')
        self.clusterer_scaler=joblib.load('./utils/ai/models/scaler.joblib')
        self.classifier_scaler=joblib.load('./utils/ai/models/classifier_scaler.joblib')
        self.columns = self.clusterer_scaler.feature_names_in_
        self.x_train=pd.read_csv('./utils/ai/models/x_train.csv')
        self.explainer = LimeTabularExplainer(
            training_data=self.x_train,
            feature_names=self.columns,
            class_names=["Not At Risk", "At Risk"],
            mode="classification",
            discretize_continuous=False
        )
        self.cluster_map={
    0: 'Balanced but inconsistent',  
    1: 'Academically focused',     
    2:'Disciplined but inactive',
    3:'Hard Worker and Active',
    4:'Talented but unruly',
    5:'Needs Intervention',
    6:'Active but struggling',
    7:'Diligent but underperforming',
      
}
        
    
    def get_data(self):
        result=self.db.query(Student).all()
        data = [student.__dict__ for student in result]
        for record in data:
            record.pop('_sa_instance_state', None)
        return pd.DataFrame(data)
    
    
    def validate_input(self, x):
        """Validate the input data."""
        if x.shape[1] != len(self.columns):
            raise ValueError("Input data has incorrect dimensions.")
        if pd.isna(x).any():
            raise ValueError("Input contains NaN values.")

    def get_cluster(self, x):
        """
        Predict the cluster for the input data.

        Args:
            x (array-like): Input data for clustering.

        Returns:
            int: The predicted cluster.
        """

        try:
            x = self.clusterer_scaler.transform(x)
            
            cluster = self.clusterer.predict(x)
            return list(map(lambda i: self.cluster_map[i],cluster))
        except Exception as e:
            raise RuntimeError(f"Error in get_cluster: {e}")

    def at_risk_classify(self, x):
        """
        Classify whether the student is at risk.

        Args:
            x (array-like): Input data for classification.

        Returns:
            int: 1 if at risk, 0 otherwise.
        """

        try:
            
            x = self.classifier_scaler.transform(x)
            
            pred = self.classifier.predict(x)
            return pred
        except Exception as e:
            raise RuntimeError(f"Error in at_risk_classify: {e}")
        
    


    def get_explanation(self, x):
        """
        Generate a LIME explanation for the input data.

        Args:
            x (array-like): Input data for explanation.

        Returns:
            lime.explanation.Explanation: The LIME explanation object.
        """

        try:
             
            x=self.classifier_scaler.transform(x.reshape(1, -1))
            explanation = self.explainer.explain_instance(
                x[0],
                self.classifier.predict_proba,
                num_features=len(self.columns)
            )
            return explanation.as_list()
        except Exception as e:
            raise RuntimeError(f"Error in get_explanation: {e}")
        
    def get_predictions(self,):
        
        preds=[]
        df=self.get_data()
        data=df[self.columns].values
        clusters=self.get_cluster(data)
        classes=self.at_risk_classify(data)
        try:
            for i in range(len(data)):
                pred={}
                pred['cluster']=clusters[i]
                pred['risk']=classes[i]==1
                pred['student_id']=df.loc[i,'id']
                pred['risk_explanation']=str(self.get_explanation(df[self.columns].iloc[i,:].values))
                pred['created_at']=datetime.datetime.now()
                preds.append(pred)
            return preds
        except Exception as e:
            raise RuntimeError(f'Exception Occured while collecting Predictions:{e}')
    
    def insert_predictions(self,preds):
        try:
            for pred in preds:
                execute=insert(StudentPredctions).values(pred)
                execute = execute.on_conflict_do_update(
                index_elements=['student_id'],  
                set_={
                    'cluster': pred['cluster'],
                    'risk': pred['risk'],
                    'risk_explanation': pred['risk_explanation']
                })
                self.db.execute(execute)
            
            self.db.commit()
            
        except Exception as e:
            raise RuntimeError(f'An Exception occured while inserting predictions')
        
    
    def run_whole_inference(self):
        try:
          pred=self.get_predictions()
          self.insert_predictions(pred)
        except Exception as e:
            raise RuntimeError(f"An Exception occured:{e}")
        finally:
            self.db.close()
        
        
        
            
        
            
            
    
    