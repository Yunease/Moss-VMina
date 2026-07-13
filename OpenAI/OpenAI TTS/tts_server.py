from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

import requests
import config


app = FastAPI(
    title="Moss VMina TTS",
    version="1.0"
)


class SpeechRequest(BaseModel):

    model: str = "gpt-sovits"

    input: str

    voice: str = "moss"

    response_format: str = "wav"

    speed: float = 1.0



@app.get("/")
def root():

    return {
        "service": "Moss VMina TTS",
        "openai_compatible": True
    }



@app.get("/v1/models")
def models():

    return {

        "object": "list",

        "data":[
            {
                "id":"gpt-sovits",
                "object":"model",
                "owned_by":"local"
            }
        ]

    }



@app.post("/v1/audio/speech")
def speech(req: SpeechRequest):

    try:

        payload = {

            "text": req.input,

            "text_lang": config.TEXT_LANG,


            "ref_audio_path":
                config.REF_AUDIO_PATH,


            "prompt_text":
                config.REF_TEXT,


            "prompt_lang":
                config.REF_LANG,


            "media_type":
                "wav",


            "speed_factor":
                req.speed
        }


        r = requests.post(
            config.GSV_URL,
            json=payload,
            timeout=120
        )


        if r.status_code != 200:

            raise HTTPException(
                status_code=500,
                detail=r.text
            )


        return Response(

            content=r.content,

            media_type="audio/wav"

        )


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )



if __name__ == "__main__":

    import uvicorn


    uvicorn.run(

        "tts_server:app",

        host=config.HOST,

        port=config.PORT,

        reload=False

    )