<?php
ini_set('display_errors',1); error_reporting(E_ALL); session_start();

if(!isset($_GET['uid']))
{
    header('Content-Type:text/html;charset=UTF-8'); echo <<<'HTML'
    <!DOCTYPE html><html><head><meta charset="UTF-8"><title>Init…</title>
    <script>
        const qs=new URLSearchParams(location.search);      
        qs.set('uid',Math.random().toString(36).substr(2,9));
        location.replace(location.pathname+'?'+qs.toString());
    </script></head><body>Loading…</body></html>
    HTML; exit;
}
$uid=$_GET['uid'];

function api(string $m,string $ep,array $body=null):array
{
    $ch=curl_init('http://localhost:8000'.$ep);
    curl_setopt_array($ch,[CURLOPT_RETURNTRANSFER=>1,CURLOPT_CUSTOMREQUEST=>$m]);
    if($body)
    {
        $j=json_encode($body); curl_setopt($ch,CURLOPT_POSTFIELDS,$j);
        curl_setopt($ch,CURLOPT_HTTPHEADER,['Content-Type: application/json', 'Content-Length: '.strlen($j)]);
    }
    $r=curl_exec($ch); if($r===false)throw new RuntimeException(curl_error($ch));
    if(curl_getinfo($ch,CURLINFO_HTTP_CODE)>=400)throw new RuntimeException($r);
    curl_close($ch); return json_decode($r,true);
}

$_SESSION['games']??=[]; $_SESSION['results']??=[];
if(!isset($_SESSION['games'][$uid]))
{
    $_SESSION['games'][$uid]=api('POST','/add_game')['idx'];
    $_SESSION['results'][$uid]=null;
}
$idx = $_SESSION['games'][$uid];
$result = &$_SESSION['results'][$uid];

if($_SERVER['REQUEST_METHOD']==='POST')
{
    if(isset($_POST['from_r']))
    {
        $turn=api('GET',"/state/$idx")['turn']??0;
        if($turn===0 && $result===null)
        {
            $move=[(int)$_POST['from_r'], (int)$_POST['from_c'], (int)$_POST['to_r'], (int)$_POST['to_c']];
            $resp=api('POST','/play_move',['idx'=>$idx,'move'=>$move]);
            $result=$resp['result'];
        }
    }
    elseif(isset($_POST['reset']))
    {
        unset($_SESSION['games'][$uid],$_SESSION['results'][$uid]);
    }
    header('Location: '.$_SERVER['PHP_SELF'].'?uid='.$uid); exit;
}

$state=api('GET',"/state/$idx");
$raw  =$state['board']??[];
$turn =$state['turn'] ??0;
$board=array_chunk(array_map('chr',$raw),8);

if($result===null && $turn===1)
{
    $resp=api('POST','/play_mcts',['idx'=>$idx]); $result=$resp['result'];
    header('Location: '.$_SERVER['PHP_SELF'].'?uid='.$uid); exit;
}

$g=['K'=>'♚','Q'=>'♛','R'=>'♜','B'=>'♝','N'=>'♞','P'=>'♟','k'=>'♚','q'=>'♛','r'=>'♜','b'=>'♝','n'=>'♞','p'=>'♟'];
function glyph(string $c, bool $isWhite):string
{
    global $g; $span=$isWhite?'w':'b';
    return '<span class="'.$span.'">'.$g[$c].'</span>';
}

$msg=$result=== 1?"♔ White wins!":($result===-1?"♚ Black wins!":($result===0?"½–½ Draw":null));
?>
<!DOCTYPE html><html><head><meta charset="UTF-8">
<title>Chess game <?= $idx ?> (uid <?=htmlspecialchars($uid)?>)</title>
<style>
  body{font-family:Segoe UI,Arial;text-align:center}
  table{border-collapse:collapse;margin:1rem auto}
  td{width:3rem;height:3rem;font-size:2.2rem;text-align:center;
     border:1px solid #444;user-select:none;cursor:pointer}
  .dark{background:#769656}.light{background:#eeeed2}
  /* fixed piece colors */
  .w{color:#ffffff}.b{color:#000000}
  .sel{outline:3px solid #ff0}
  button{margin:.4rem .7rem;padding:.4rem .8rem}
  .msg{font-size:1.3rem;margin:1rem}
  /* legal moves display */
  #board td {position: relative;}
  .target::after {content: "";position: absolute;width: 1rem;height: 1rem;top: 50%;left: 50%;transform: translate(-50%, -50%);border-radius: 50%;background: rgba(0, 0, 0, 0.25);pointer-events: none;}
</style>
</head><body>
<h2>Chess — game #<?= $idx ?> (uid <?=htmlspecialchars($uid)?>)</h2>

<form id="moveform" method="post" style="display:none">
  <input type="hidden" name="from_r"><input type="hidden" name="from_c">
  <input type="hidden" name="to_r"><input type="hidden" name="to_c">
</form>

<table id="board">
<?php for($r=0;$r<8;$r++): ?><tr>
<?php for($c=0;$c<8;$c++):
        $cls=(($r+$c)&1)?'dark':'light';
        $piece=$board[$r][$c];
        $html= ($piece===' ')?' ':glyph($piece,ctype_upper($piece)); ?>
  <td class="<?= $cls ?>" data-r="<?=$r?>" data-c="<?=$c?>"><?=$html?></td>
<?php endfor;?></tr><?php endfor;?>
</table>

<?php if($msg): ?>
  <div class="msg"><?= $msg ?></div>
  <form method="post"><button name="reset">New Game</button></form>
<?php elseif($turn===0): ?>
  <div class="msg">Your move (White)</div>
  <form method="post"><button name="reset">Resign / New Game</button></form>
<?php else: ?>
  <div class="msg">🤖 Bot is thinking…</div>
<?php endif; ?>

<script>
const uid      = "<?= htmlspecialchars($uid) ?>";
const gameIdx  = <?= $idx ?>;
const finished = <?= $result===null?'false':'true' ?>;
const myTurn   = <?= $turn ?>===0;

let sel = null;
let cache = {};

function coord(td){ return [ +td.dataset.r, +td.dataset.c ]; }
function key(r,c){ return `${r},${c}`; }

async function fetchMoves(r,c)
{
    if(cache[key(r,c)]) return cache[key(r,c)];
    const res = await fetch(`proxy_moves.php?idx=${gameIdx}`);
    const data= await res.json();
    data.moves.forEach(m=>{const k = key(m[0],m[1]); (cache[k]??=[]).push([m[2],m[3]]);});
    return cache[key(r,c)]??[];
}

function clearHighlights()
{
    document.querySelectorAll('.sel').forEach(td=>td.classList.remove('sel'));
    document.querySelectorAll('.target').forEach(td=>td.classList.remove('target'));
}

document.querySelectorAll('#board td').forEach(td=>{
  td.addEventListener('click', async ()=>{
    if(finished || !myTurn) return;

    const [r,c] = coord(td);

    if(!sel)
    {
        const piece = td.textContent.trim();
        if(!piece) return;
        const moves = await fetchMoves(r,c);
        if(moves.length===0) return;

        sel = td; sel.classList.add('sel');
        moves.forEach(([tr,tc])=>{document.querySelector(`#board td[data-r="${tr}"][data-c="${tc}"]`).classList.add('target');});
        return;
    }

    const targets = cache[key(...coord(sel))]??[];
    if(targets.some(([tr,tc])=>tr===r && tc===c))
    {
        const form=document.getElementById('moveform');
        form.from_r.value=sel.dataset.r; form.from_c.value=sel.dataset.c;
        form.to_r.value  =td.dataset.r;  form.to_c.value  =td.dataset.c;
        form.submit();
    }
    clearHighlights(); sel=null;
  });
});
</script>
</body></html>