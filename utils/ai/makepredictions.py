import joblib
import pandas as pd
import numpy as np
from sqlalchemy.dialects.postgresql import insert
from lime.lime_tabular import LimeTabularExplainer
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel
from langchain_groq import ChatGroq
import datetime
from collections import defaultdict

from utils.models import Student,StudentPredctions,SessionLocal,Subject,SubjectAnalysis
from utils.ai.tools import strengths_chain
from utils.routers.students import calculate_exam_avg


class RunPredictions():
    def __init__(self):
        self.db=SessionLocal()
        self.clusterer=joblib.load('./utils/ai/models/clusterer.joblib')
        self.classifier=joblib.load('./utils/ai/models/risk_classifier.joblib')
        self.clusterer_scaler=joblib.load('./utils/ai/models/scaler.joblib')
        self.classifier_scaler=joblib.load('./utils/ai/models/classifier_scaler.joblib')
        self.columns = self.clusterer_scaler.feature_names_in_
        self.x_train=pd.read_csv('./utils/ai/models/x_train.csv')
        self.exam_model=joblib.load('./utils/ai/models/exams.joblib')
        self.explainer = LimeTabularExplainer(
            training_data=self.x_train,
            feature_names=self.columns,
            class_names=["Not At Risk", "At Risk"],
            mode="classification",
            discretize_continuous=False
        )
        self.pred_to_analysis={4:'Excel and Improving',
                          3:'Improving Consistently',
                          2:'Excels but declining',
                          0:'Poor and declining',
                          1:'Needs hard work'}
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
        students=self.db.query(Student).all()
        students=students
        exam_data=[]
        for student in students:
            student_dict = defaultdict(lambda: None)  # Default to None if no score
            student_dict['id'] = student.id
            student_subjects = []
            subject_ids = []
            
            for score in student.exam_scores:
                subject_name,subject_id = self.db.query(Subject.name,Subject.id).where(Subject.id == score.subject_id).first()
                if subject_name not in student_subjects:
                    student_subjects.append(subject_name)
                if subject_id not in subject_ids:
                    subject_ids.append(subject_id)
                subject_index = student_subjects.index(subject_name) + 1 
                column_name = f'exam{score.exam_number}_subject{subject_index}'
                student_dict[column_name] = score.score
            student_dict['subjects'] = student_subjects  
            student_dict['subject_ids'] = subject_ids  
            exam_data.append(student_dict)
        data = [student.__dict__ for student in students]
        for record in data:
            record.pop('_sa_instance_state', None)
        return pd.merge(pd.DataFrame(data),pd.DataFrame(exam_data),on='id',how='inner')
    
    
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
        
    

    def get_summary(self,cluster,risk,x):
        try:
            summary=strengths_chain.invoke({'cluster':cluster,'risk':risk,'report':x})
            return summary.summary
        except Exception as e:
            raise RuntimeError(f'Error in generating summary, {e}')
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
        
    def get_report(self,x):
        
        try:
            exams=calculate_exam_avg(self.db,x['id'])
            return {
                'name':x['name'],
                'avg_grades':float(x['avg_grades']),
                'behavioral':float(x['behavioral']),
                'attendance':float(x['attendance']),
                'extracurricular':float(x['extracurricular']),
                'first_exam':exams[0],
                'second_exam':exams[1],
                'third_exam':exams[2],
                'fourth_exam':exams[3]
                
            }
        except Exception as e:
            raise RuntimeError(f"Error in generating report for summary,{e}")
        
    def get_predictions(self,):
        
        preds=[]
        df=self.get_data()
        exam_data=df.iloc[:,17:]
        
        data=df[self.columns].values
        clusters=self.get_cluster(data)
        classes=self.at_risk_classify(data)
        try:
            for i in range(len(data)):
                pred={}
                pred['cluster']=clusters[i]
                pred['risk']=classes[i]==1
                pred['student_id']=df.loc[i,'id']
                pred['subject_analysis']=self.ind_subject(exam_data.loc[i,:])
                # report=self.get_report(df.iloc[i,:])
                pred['risk_explanation']=str(self.get_explanation(df[self.columns].iloc[i,:].values))
                
                # pred['summary']=str(self.get_summary(clusters[i],classes[i]==1,report))
                pred['created_at']=datetime.datetime.now()
                preds.append(pred)
            return preds
        except Exception as e:
            raise RuntimeError(f'Exception Occured while collecting Predictions:{e}')
    
    def insert_predictions(self,preds):
        try:
            for pred in preds:
                student_pred_data = {
                'student_id': pred['student_id'],
                'cluster': pred['cluster'],
                'risk': pred['risk'],
                'risk_explanation': pred['risk_explanation'],
                'created_at': pred['created_at']
            }
                execute=insert(StudentPredctions).values(**student_pred_data)
                execute = execute.on_conflict_do_update(
                index_elements=['student_id'],  
                set_={
                    'cluster': student_pred_data['cluster'],
                    'risk': student_pred_data['risk'],
                    # 'summary':pred['summary'],
                    'risk_explanation': student_pred_data['risk_explanation']
                })
                self.db.execute(execute)
                for subject_name, analysis_data in pred['subject_analysis'].items():
                    subject_entry = {
                        'student_id': pred['student_id'],
                        'subject_id': analysis_data['sub_id'],
                        'marks': str([round(float(i),2) for i in analysis_data['marks']]),
                        'analysis': analysis_data['risk_analysis']
                    }
                    stmt = insert(SubjectAnalysis).values(**subject_entry)
                    stmt = stmt.on_conflict_do_update(
                        constraint='uq_student_subject',
                        set_={
                            'marks': str(subject_entry['marks']),
                            'analysis': subject_entry['analysis']
                        }
                    )
                    self.db.execute(stmt)
            
            self.db.commit()
            
        except Exception as e:
            raise RuntimeError(f'An Exception occured while inserting predictions')
        
    def ind_subject(self,x):
        pred_dict={}
        subjects=x['subjects']
        ids=x['subject_ids']
        
        for i in range(1,len(subjects)+1):
            
            sub=x.loc[[f'exam1_subject{i}', f'exam2_subject{i}', f'exam3_subject{i}', f'exam4_subject{i}']]
            pred=self.exam_model.predict(sub.values.reshape(1,-1)/100)
            pred_dict[subjects[i-1]]={'risk_analysis':self.pred_to_analysis[pred[0]],
            'marks':list(sub.values),'sub_id':ids[i-1]}
        return pred_dict
        
        
    
    def run_whole_inference(self):
        try:
          pred=self.get_predictions()
          self.insert_predictions(pred)
        except Exception as e:
            raise RuntimeError(f"An Exception occured:{e}")
        finally:
            self.db.close()
            
        

        
        
        
            
        
            
            
    
    