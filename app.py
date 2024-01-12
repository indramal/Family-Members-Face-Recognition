import boto3
import json
import os
import face_recognition
from urllib.parse import urlparse

from fastapi import FastAPI
from mangum import Mangum
import uvicorn

from aws_lambda_powertools import Logger

logger = Logger()

app = FastAPI()
handler = Mangum(app)


@app.get("/")
async def index():
    return "Home"


@app.get("/api")
async def student_data(inputfname: str, personname: str, token: str):
    key = "RRshJy4beYdlNbu"

    if token == key:
        logger.info("INFO: Program is Running...")

        s3 = boto3.client(
            "s3",
            aws_access_key_id="AKIAXDPKO46TVVL25E4L",
            aws_secret_access_key="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",
        )

        s3bucketname = "relationphotos"
        filenameinput = inputfname
        s3checkdir = "Check"
        donwload_folder = "/tmp"

        logger.info("INFO: Input file:" + filenameinput)

        prefix1 = f"{s3checkdir}/{filenameinput}"
        checkfile = f"{donwload_folder}/{filenameinput}"

        s3.download_file(s3bucketname, prefix1, checkfile)

        if os.path.exists(checkfile):
            relations_folder = "/tmp/relations"

            if not os.path.exists(relations_folder):
                os.makedirs(relations_folder)

            s3relationsdir = "Relations"
            s3personanem = personname
            prefix2 = f"{s3relationsdir}/{s3personanem}"

            logger.info("INFO: Input person:" + s3personanem)

            result = []

            response = s3.list_objects_v2(Bucket=s3bucketname, Prefix=prefix2)

            if "Contents" in response:
                for obj in response["Contents"]:
                    if obj["Key"].endswith((".png", ".jpg", ".jpeg")):
                        urlforrelation = obj["Key"]

                        parsed_url = urlparse(urlforrelation)
                        path = parsed_url.path
                        directories = path.split("/")

                        filename = os.path.basename(path)
                        relation_name = directories[-3]
                        person_name = directories[-2]
                        relation_person = directories[-4]

                        relationfile = f"{relations_folder}/{filename}"

                        s3.download_file(s3bucketname, urlforrelation, relationfile)

                        known_image = face_recognition.load_image_file(checkfile)
                        unknown_image = face_recognition.load_image_file(relationfile)

                        biden_encoding = face_recognition.face_encodings(known_image)[0]
                        unknown_encoding = face_recognition.face_encodings(
                            unknown_image
                        )[0]

                        relcheckresults = face_recognition.compare_faces(
                            [biden_encoding], unknown_encoding
                        )

                        if relcheckresults[0] == True:
                            url = s3.generate_presigned_url(
                                "get_object",
                                Params={"Bucket": s3bucketname, "Key": urlforrelation},
                                ExpiresIn=3600,  # URL expiration time in seconds (adjust as needed)
                            )
                            result.append(
                                {
                                    "status": "Found",
                                    "file": filename,
                                    "url": url,
                                    "relation": relation_name,
                                    "name": person_name,
                                    "relation_person": relation_person,
                                }
                            )

                if len(result) == 0:
                    result.append({"status": "NotFound"})
            else:
                result.append({"status": "NoRelations"})

            return {"Status": "Done", "Output": json.dumps(result)}
        else:
            return {"Status": "Error", "Output": "Input file name error or not found"}

    else:
        return {"Status": "Error", "Output": "Tocken Error"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
