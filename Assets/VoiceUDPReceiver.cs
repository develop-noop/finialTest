using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;
using TMPro;   // TextMeshPro 사용

// Python에서 보내는 Q&A JSON을 받기 위한 클래스
[System.Serializable]
public class QAMessage
{
    public string type;        // "qa"
    public int mode;           // 2 또는 3
    public string q;           // 질문
    public string sentiment;   // "호" / "중립" / "불호"
    public string[] keywords;  // 키워드 배열
    public string a;           // 대답
    public string persona;     // 모드3일 때 "cute"/"tsundere"/"naive"
}

public class VoiceUDPReceiver : MonoBehaviour
{
    public int listenPort = 5005;
    private UdpClient udpClient;
    private Thread receiveThread;
    private bool running = false;

    // 이제는 단순 명령어뿐 아니라 JSON 전체 메시지를 저장
    private string latestMessage = null;
    private readonly object lockObj = new object();

    public Animator animator;
    public SpeechBubbleManager bubbleManager;

    // 게임 화면에 표시할 UI 텍스트 (TextMeshProUGUI)
    public TMP_Text questionText;    // 질문 텍스트
    public TMP_Text sentimentText;   // 감정 텍스트
    public TMP_Text keywordsText;    // 키워드 텍스트
    public TMP_Text answerText;      // 대답 텍스트

    void Start()
    {
        udpClient = new UdpClient(listenPort);
        running = true;
        receiveThread = new Thread(ReceiveLoop);
        receiveThread.IsBackground = true;
        receiveThread.Start();
    }

    void ReceiveLoop()
    {
        IPEndPoint remoteEP = new IPEndPoint(IPAddress.Any, listenPort);
        while (running)
        {
            try
            {
                byte[] data = udpClient.Receive(ref remoteEP);
                string msg = Encoding.UTF8.GetString(data);

                lock (lockObj)
                {
                    latestMessage = msg;
                }

                // Debug.Log("수신된 원본 메시지: " + msg);
            }
            catch (SocketException) { }
        }
    }

    void Update()
    {
        string msg = null;
        lock (lockObj)
        {
            if (latestMessage != null)
            {
                msg = latestMessage;
                latestMessage = null;
            }
        }

        if (msg != null)
        {
            HandleMessage(msg);
        }
    }

    void HandleMessage(string msg)
    {
        if (string.IsNullOrEmpty(msg))
            return;

        msg = msg.Trim();
        // Debug.Log("HandleMessage 받은 내용: " + msg);

        // 1) JSON(Q&A)인지 먼저 확인
        if (msg.StartsWith("{"))
        {
            try
            {
                var qa = JsonUtility.FromJson<QAMessage>(msg);
                if (qa != null && qa.type == "qa")
                {
                    Debug.Log($"[QA 모드{qa.mode}] 질문: {qa.q}");
                    Debug.Log($"[QA 모드{qa.mode}] 감정: {qa.sentiment}");
                    Debug.Log($"[QA 모드{qa.mode}] 키워드: {string.Join(", ", qa.keywords ?? new string[0])}");
                    Debug.Log($"[QA 모드{qa.mode}] 대답: {qa.a}");

                    if (animator != null)
                    {
                        if (qa.sentiment == "호")
                        {
                            animator.Play("GoatSheep_Eating");
                        }
                        else if (qa.sentiment == "불호")
                        {
                            animator.Play("GoatSheep_Attack01");
                        }
                    }

                        if (!string.IsNullOrEmpty(qa.persona))
                        Debug.Log($"[QA 모드{qa.mode}] 성격: {qa.persona}");

                    //  여기서 게임 실행창(UI)에 질문, 감정, 키워드, 대답 표시
                    if (questionText != null)
                        questionText.text = $"Q: {qa.q}";

                    if (sentimentText != null)
                        sentimentText.text = $"감정: {qa.sentiment}";

                    if (keywordsText != null)
                        keywordsText.text = "키워드: " + string.Join(", ", qa.keywords ?? new string[0]);

                    if (answerText != null)
                        answerText.text = $"A: {qa.a}";

                    // 말풍선 매니저에도 전달 (이미 사용 중이면 그대로 두기)
                    if (bubbleManager != null)
                    {
                        bubbleManager.ShowQA(
                            qa.q,
                            qa.sentiment,
                            qa.keywords,
                            qa.a,
                            qa.persona
                        );
                    }
                    else
                    {
                        Debug.LogWarning("bubbleManager가 설정되지 않았습니다.");
                    }

                    return; // Q&A 처리 끝났으니까 여기서 종료
                }
            }
            catch (System.Exception e)
            {
                Debug.LogWarning("QA JSON 파싱 실패, 일반 명령으로 처리 시도: " + e.Message);
                // JSON 파싱 실패하면 아래에서 그냥 문자열 명령처럼 처리
            }
        }

        // 2) 여기까지 왔다는 건 JSON이 아니거나, JSON 파싱 실패 → 단순 명령으로 처리
        Debug.Log("받은 명령어: " + msg);

        if (animator == null)
            return;

        if (msg == "HELLO")
        {
            Debug.Log("HELLO 명령어 → 캐릭터 인사 애니메이션");
            animator.SetTrigger("Hello");
        }
        else if (msg == "EAT")
        {
            Debug.Log("EAT 명령어 → 캐릭터 식사 애니메이션");
            animator.SetTrigger("Food");
        }
        else if (msg == "CUTE")
        {
            Debug.Log("CUTE 명령어 → 캐릭터 귀여운 반응 애니메이션");
            animator.SetTrigger("Cute");
        }
        else
        {
            Debug.Log("알 수 없는 명령 또는 처리 불가 메시지: " + msg);
        }
    }

    void OnApplicationQuit()
    {
        running = false;
        if (udpClient != null)
        {
            udpClient.Close();
        }
    }
}
