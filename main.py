from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from google import genai

from database import SessionLocal, User


load_dotenv()


app = FastAPI()


templates = Jinja2Templates(
    directory="templates"
)


client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.get("/")
def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request
        }
    )


# --------------------------------------------------
# WORKOUT REQUEST
# --------------------------------------------------

class WorkoutRequest(BaseModel):

    user_profile: str

    feedback: str = ""


# --------------------------------------------------
# GENERATE WORKOUT
# --------------------------------------------------

@app.post("/generate-workout")
def generate_workout(request: WorkoutRequest):

    prompt = f"""
    Create a structured 7-day workout plan.

    User profile:
    {request.user_profile}

    Previous feedback:
    {request.feedback}

    Requirements:
    - Provide Day 1 to Day 7
    - Include exercises
    - Include sets and repetitions where appropriate
    - Keep the plan practical and actionable
    - Clearly format each day
    """


    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )


    workout_plan = response.text


    return {
        "workout_plan": workout_plan
    }


# --------------------------------------------------
# NUTRITION REQUEST
# --------------------------------------------------

class NutritionRequest(BaseModel):

    user_goal: str


# --------------------------------------------------
# GENERATE NUTRITION
# --------------------------------------------------

@app.post("/nutrition")
def nutrition(request: NutritionRequest):

    prompt = f"""
    Give concise and practical nutrition tips
    for a user with this goal:

    {request.user_goal}

    Provide short, actionable tips.
    """


    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )


    return {
        "nutrition_tips": response.text
    }


# --------------------------------------------------
# SAVE USER + GENERATE WORKOUT + NUTRITION
# --------------------------------------------------

@app.post("/create-plan")
def create_plan(

    request: Request,

    name: str = Form(...),

    age: str = Form(...),

    gender: str = Form(...),

    height: str = Form(...),

    weight: str = Form(...),

    goal: str = Form(...),

    fitness_level: str = Form(...),

    equipment: str = Form("")

):

    user_profile = f"""
    Name: {name}
    Age: {age}
    Gender: {gender}
    Height: {height} cm
    Weight: {weight} kg
    Fitness Goal: {goal}
    Fitness Level: {fitness_level}
    Available Equipment: {equipment}
    """


    # --------------------------------------------------
    # GENERATE WORKOUT
    # --------------------------------------------------

    prompt = f"""
    Create a structured 7-day workout plan.

    User profile:
    {user_profile}

    Requirements:
    - Provide Day 1 to Day 7
    - Include exercises
    - Include sets and repetitions
    - Include rest days where appropriate
    - Keep the plan practical and actionable
    - Clearly format each day
    """


    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )


    workout_plan = response.text


    # --------------------------------------------------
    # GENERATE NUTRITION TIPS
    # --------------------------------------------------

    nutrition_prompt = f"""
    Give concise and practical nutrition tips
    for a user with this fitness goal:

    {goal}

    User profile:
    Age: {age}
    Gender: {gender}
    Height: {height} cm
    Weight: {weight} kg
    Fitness Level: {fitness_level}

    Requirements:
    - Provide short and practical nutrition tips
    - Focus on healthy general guidance
    - Include hydration advice
    - Keep the response easy to understand
    """


    nutrition_response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=nutrition_prompt
    )


    nutrition_tips = nutrition_response.text


    # --------------------------------------------------
    # SAVE USER TO DATABASE
    # --------------------------------------------------

    db = SessionLocal()


    user = User(

        name=name,

        age=age,

        gender=gender,

        height=height,

        weight=weight,

        goal=goal,

        fitness_level=fitness_level,

        equipment=equipment,

        workout_plan=workout_plan,

        nutrition_tips=nutrition_tips

    )


    db.add(user)

    db.commit()

    db.refresh(user)

    db.close()


    # --------------------------------------------------
    # SHOW RESULT PAGE
    # --------------------------------------------------

    return templates.TemplateResponse(

        request=request,

        name="result.html",

        context={

            "request": request,

            "user": user,

            "workout_plan": workout_plan,

            "nutrition_tips": nutrition_tips,

            "user_id": user.id

        }

    )


# --------------------------------------------------
# UPDATE WORKOUT WITH FEEDBACK
# --------------------------------------------------

@app.post("/update-workout")
def update_workout(

    request: Request,

    user_id: int = Form(...),

    feedback: str = Form(...)

):

    db = SessionLocal()


    user = db.query(User).filter(
        User.id == user_id
    ).first()


    if user is None:

        db.close()

        return {"error": "User not found"}


    user_profile = f"""
    Name: {user.name}
    Age: {user.age}
    Gender: {user.gender}
    Height: {user.height} cm
    Weight: {user.weight} kg
    Fitness Goal: {user.goal}
    Fitness Level: {user.fitness_level}
    Available Equipment: {user.equipment}
    """


    prompt = f"""
    Update the user's workout plan based on their feedback.

    User profile:
    {user_profile}

    Previous workout plan:
    {user.workout_plan}

    User feedback:
    {feedback}

    Requirements:
    - Provide an updated 7-day workout plan
    - Consider the user's feedback
    - Keep it practical
    - Clearly format Day 1 to Day 7
    """


    # --------------------------------------------------
    # GENERATE UPDATED WORKOUT
    # --------------------------------------------------

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        updated_plan = response.text

    except Exception as e:

        db.close()

        print("Gemini update error:", e)

        return {
            "error": "Gemini is temporarily unavailable. Please try again in a few moments."
        }


    # --------------------------------------------------
    # UPDATE DATABASE
    # --------------------------------------------------

    user.workout_plan = updated_plan

    user.feedback = feedback


    db.commit()

    db.refresh(user)


    nutrition_tips = user.nutrition_tips


    db.close()


    # --------------------------------------------------
    # SHOW UPDATED RESULT
    # --------------------------------------------------

    return templates.TemplateResponse(

        request=request,

        name="result.html",

        context={

            "request": request,

            "user": user,

            "workout_plan": updated_plan,

            "nutrition_tips": nutrition_tips,

            "user_id": user.id

        }

    )


# --------------------------------------------------
# ADMIN - ALL USERS
# --------------------------------------------------

@app.get("/all-users")
def all_users(request: Request):

    db = SessionLocal()


    users = db.query(User).all()


    db.close()


    return templates.TemplateResponse(

        request=request,

        name="all_users.html",

        context={

            "request": request,

            "users": users

        }

    )
