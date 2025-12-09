using UnityEngine;
using TMPro;
using System.Collections;
using UnityEngine.Networking;

public class QADisplayEn : MonoBehaviour
{
    public TMP_Text questionText;
    public TMP_Text answerText;
    public Animator animator;   // trot_forward 실행할 Animator

    private bool isRequesting = false;

    void Update()
    {
        // Keypad 4
        if (Input.GetKeyDown(KeyCode.Keypad4))
        {
            if (!isRequesting)
            {
                StartCoroutine(RequestQAFromMic());
            }
        }
    }

    IEnumerator RequestQAFromMic()
    {
        isRequesting = true;

        if (questionText != null)
            questionText.text = "Listening 4 seconds...";
        if (answerText != null)
            answerText.text = "";

        UnityWebRequest req = new UnityWebRequest("http://127.0.0.1:5000/qa_from_mic", "POST");
        req.uploadHandler = new UploadHandlerRaw(new byte[0]);
        req.downloadHandler = new DownloadHandlerBuffer();
        req.SetRequestHeader("Content-Type", "application/json");

        yield return req.SendWebRequest();

        if (req.result == UnityWebRequest.Result.Success)
        {
            Debug.Log($"[HTTP] success, code={req.responseCode}, body={req.downloadHandler.text}");

            var json = req.downloadHandler.text;
            QAResponse res = JsonUtility.FromJson<QAResponse>(json);

            if (res.ok)
            {
                if (questionText != null)
                    questionText.text = "Q: " + res.question;

                if (answerText != null)
                    answerText.text = "A(" + res.persona + "): " + res.answer;

                // 여기서 trot_forward 애니 실행 
                if (animator != null)
                {
                    animator.Play("trot_forward");
                }
            }
            else
            {
                if (questionText != null)
                    questionText.text = "Recognition failed: " + res.error;
                if (answerText != null)
                    answerText.text = "";
            }
        }
        else
        {
            Debug.LogError($"[HTTP ERROR] result={req.result}, code={req.responseCode}, error={req.error}, body={req.downloadHandler.text}");

            if (questionText != null)
                questionText.text = "Server error";
            if (answerText != null)
                answerText.text = req.error;
        }

        isRequesting = false;
    }

    [System.Serializable]
    public class QAResponse
    {
        public bool ok;
        public string question;
        public string answer;
        public string persona;
        public string error;
    }
}
